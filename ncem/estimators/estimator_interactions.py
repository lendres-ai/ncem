import tensorflow as tf
from typing import Union
import numpy as np
import scipy
from patsy import dmatrix

from ncem.estimators import Estimator
from ncem.models import ModelInteractions


class EstimatorInteractions(Estimator):
    def __init__(
            self,
            log_transform: bool = False,
    ):
        super(EstimatorInteractions, self).__init__()
        self.model_type = "linear_interactions"
        self.adj_type = 'full'
        self.log_transform = log_transform
        self.metrics = {"np": [], "tf": []}

    def _get_output_signature(self, resampled: bool = False):
        pass

    def _get_dataset(
            self,
            image_keys: np.ndarray,
            nodes_idx: Union[dict, str],
            batch_size: int,
            shuffle_buffer_size: int,
            train: bool,
            seed: Union[int, None],
            prefetch: int = 100,
            reinit_n_eval: Union[int, None] = None
    ):
        np.random.seed(seed)
        if reinit_n_eval is not None and reinit_n_eval != self.n_eval_nodes_per_graph:
            print(
                "ATTENTION: specifying reinit_n_eval will change class argument n_eval_nodes_per_graph "
                "from %i to %i"
                % (self.n_eval_nodes_per_graph, reinit_n_eval)
            )
            self.n_eval_nodes_per_graph = reinit_n_eval

        def generator():
            for key in image_keys:
                if nodes_idx[key].size == 0:  # needed for images where no nodes are selected
                    continue
                idx_nodes = np.arange(0, self.a[key].shape[0])

                if train:
                    index_list = [
                        np.asarray(np.random.choice(
                            a=nodes_idx[key],
                            size=self.n_eval_nodes_per_graph,
                            replace=True,
                        ), dtype=np.int32)
                    ]
                else:
                    # dropping
                    index_list = [np.asarray(
                            nodes_idx[key][self.n_eval_nodes_per_graph * i:self.n_eval_nodes_per_graph * (i + 1)],
                            dtype=np.int32
                        ) for i in range(len(nodes_idx[key]) // self.n_eval_nodes_per_graph)
                    ]

                for indices in index_list:
                    h_1 = self.h_1[key][idx_nodes]
                    diff = self.max_nodes - h_1.shape[0]
                    zeros = np.zeros((diff, h_1.shape[1]))
                    h_1 = np.asarray(np.concatenate((h_1, zeros), axis=0), dtype="float32")
                    h_1 = h_1[indices]
                    if self.log_transform:
                        h_1 = np.log(h_1 + 1.)

                    h_0 = self.h_0[key][idx_nodes]
                    diff = self.max_nodes - h_0.shape[0]
                    zeros = np.zeros((diff, h_0.shape[1]), dtype="float32")
                    h_0_full = np.asarray(np.concatenate((h_0, zeros), axis=0), dtype="float32")
                    h_0 = h_0_full[indices]

                    a = self.a[key][idx_nodes, :][:, idx_nodes]
                    a = a[indices, :]
                    coo = a.tocoo()
                    a_shape = np.asarray((self.n_eval_nodes_per_graph, self.max_nodes), dtype="int64")
                    a = scipy.sparse.coo_matrix((coo.data, (coo.row, coo.col)), a_shape)

                    # Assemble design matrix components for interactions:
                    dmat_neighbours = (a.toarray() > 0.).astype("int").dot(
                        h_0_full)  # n_eval_nodes_per_graph x node types
                    # discretize interactions
                    dmat_neighbours = np.asarray(dmat_neighbours > 0, dtype="int")

                    data = {'target': h_0, 'dmat_neighbours': dmat_neighbours}
                    target = np.asarray(dmatrix("target-1", data))
                    interactions = np.asarray(dmatrix("target:dmat_neighbours-1", data))
                    #interactions_data = interactions.flatten()
                    #interactions_shape = np.asarray(
                    #    (self.n_eval_nodes_per_graph, self.n_features_0 ** 2), dtype="int64"
                    #)
                    interactions = scipy.sparse.coo_matrix(interactions)
                    coo = interactions.tocoo()
                    interactions_ind = np.asarray(np.mat([coo.row, coo.col]).transpose(), dtype="int64")
                    interactions_val = np.asarray(coo.data, dtype="float32")
                    interactions_shape = np.asarray((self.n_eval_nodes_per_graph, self.n_features_0 ** 2), dtype="int64")
                    interactions = tf.SparseTensor(
                        indices=interactions_ind, values=interactions_val, dense_shape=interactions_shape
                    )

                    node_covar = self.node_covar[key][idx_nodes]
                    diff = self.max_nodes - node_covar.shape[0]
                    zeros = np.zeros((diff, node_covar.shape[1]))
                    node_covar = np.asarray(np.concatenate([node_covar, zeros], axis=0), dtype="float32")
                    node_covar = node_covar[indices]

                    sf = np.expand_dims(self.size_factors[key][idx_nodes], axis=1)
                    diff = self.max_nodes - sf.shape[0]
                    zeros = np.zeros((diff, sf.shape[1]))
                    sf = np.asarray(np.concatenate([sf, zeros], axis=0), dtype="float32")
                    sf = sf[indices, :]

                    g = np.zeros((self.n_domains,), dtype="int32")
                    g[self.domains[key]] = 1

                    yield (target, interactions, sf, node_covar, g), h_1

        dataset = tf.data.Dataset.from_generator(
            generator=generator,
            output_signature=(
                (
                    tf.TensorSpec(shape=(self.n_eval_nodes_per_graph, self.n_features_0), dtype=tf.float32),
                    tf.SparseTensorSpec(shape=(self.n_eval_nodes_per_graph, self.n_features_0 ** 2), dtype=tf.float32),
                    tf.TensorSpec(shape=(self.n_eval_nodes_per_graph, 1), dtype=tf.float32),
                    tf.TensorSpec(shape=(self.n_eval_nodes_per_graph, self.n_node_covariates), dtype=tf.float32),
                    tf.TensorSpec(shape=(self.n_domains,), dtype=tf.int32)
                ),
                tf.TensorSpec(shape=(self.n_eval_nodes_per_graph, self.n_features_1), dtype=tf.float32)
            )
        )
        if train:
            if shuffle_buffer_size is not None:
                dataset = dataset.shuffle(
                    buffer_size=shuffle_buffer_size,
                    seed=None,
                    reshuffle_each_iteration=True
                )
            dataset = dataset.repeat()
        dataset = dataset.batch(batch_size)
        dataset = dataset.prefetch(prefetch)
        return dataset

    def init_model(
            self,
            optimizer: str = 'adam',
            learning_rate: float = 0.0001,
            n_eval_nodes_per_graph: int = 32,
            use_interactions: bool = True,
            use_domain: bool = False,
            output_layer: str = 'linear',
            **kwargs
    ):
        self.n_eval_nodes_per_graph = n_eval_nodes_per_graph
        self.model = ModelInteractions(
            input_shapes=(
                self.n_features_0,  # target_dim
                self.n_features_1,  # out_node_feature_dim
                self.n_features_0 ** 2,  # interaction_dim
                self.n_eval_nodes_per_graph,  # in_node_dim
                self.n_node_covariates,  # categ_condition_dim
                self.n_domains  # domain_dim
            ),
            use_interactions=use_interactions,
            use_domain=use_domain,
            output_layer=output_layer
        )
        optimizer = tf.keras.optimizers.get(optimizer)
        tf.keras.backend.set_value(optimizer.lr, learning_rate)
        self._compile_model(optimizer=optimizer, output_layer=output_layer)
