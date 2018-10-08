from datetime import datetime

import factory
import pandas as pd
import testing.postgresql
from sqlalchemy import create_engine

from tests.results_tests.factories import (
    EvaluationFactory,
    ModelFactory,
    ModelGroupFactory,
    init_engine,
    session,
    MatrixFactory,
)

from triage.component.audition.pre_audition import PreAudition
from triage.component.catwalk.db import ensure_db


def test_PreAudition():
    with testing.postgresql.Postgresql() as postgresql:
        db_engine = create_engine(postgresql.url())
        ensure_db(db_engine)
        init_engine(db_engine)
        # set up data, randomly generated by the factories but conforming
        # generally to what we expect model_metadata schema data to look like
        num_model_groups = 10
        model_types = [
            "classifier type {}".format(i) for i in range(0, num_model_groups)
        ]
        model_configs = [
            {"label_definition": "label_1"}
            if i % 2 == 0
            else {"label_definition": "label_2"}
            for i in range(0, num_model_groups)
        ]
        model_groups = [
            ModelGroupFactory(model_type=model_type, model_config=model_config)
            for model_type, model_config in zip(model_types, model_configs)
        ]
        train_end_times = [
            datetime(2013, 1, 1),
            datetime(2013, 7, 1),
            datetime(2014, 1, 1),
            datetime(2014, 7, 1),
            datetime(2015, 1, 1),
            datetime(2015, 7, 1),
            datetime(2016, 7, 1),
            datetime(2016, 1, 1),
        ]

        models = [
            ModelFactory(model_group_rel=model_group, train_end_time=train_end_time)
            for model_group in model_groups
            for train_end_time in train_end_times
        ]
        metrics = [
            ("precision@", "100_abs"),
            ("recall@", "100_abs"),
            ("precision@", "50_abs"),
            ("recall@", "50_abs"),
            ("fpr@", "10_pct"),
        ]

        class ImmediateEvalFactory(EvaluationFactory):
            evaluation_start_time = factory.LazyAttribute(
                lambda o: o.model_rel.train_end_time
            )

        for model in models:
            for (metric, parameter) in metrics:
                ImmediateEvalFactory(
                    model_rel=model, metric=metric, parameter=parameter
                )

        session.commit()

        pre_aud = PreAudition(db_engine)

        # Expect the number of model groups with label_1
        assert len(pre_aud.get_model_groups_from_label("label_1")) == sum(
            [x["label_definition"] == "label_1" for x in model_configs]
        )

        # Expect the number of model groups with certain experiment_hash
        experiment_hash = list(
            pd.read_sql(
                "SELECT experiment_hash FROM model_metadata.models limit 1",
                con=db_engine,
            )["experiment_hash"]
        )[0]
        assert len(pre_aud.get_model_groups_from_experiment(experiment_hash)) == 1

        # Expect the number of model groups for customs SQL
        query = """
            SELECT DISTINCT(model_group_id)
            FROM model_metadata.models
            WHERE train_end_time >= '2013-01-01'
            AND experiment_hash = '{}'
        """.format(
            experiment_hash
        )
        assert len(pre_aud.get_model_groups(query)) == 1

        # Expect the number of train_end_times after 2014-01-01
        assert len(pre_aud.get_train_end_times(after="2014-01-01")) == 6

        query = """
            SELECT DISTINCT train_end_time
            FROM model_metadata.models
            WHERE model_group_id IN ({})
                AND train_end_time >= '2014-01-01'
            ORDER BY train_end_time
            """.format(
            ", ".join(map(str, pre_aud.model_groups))
        )

        assert len(pre_aud.get_train_end_times(query=query)) == 6
