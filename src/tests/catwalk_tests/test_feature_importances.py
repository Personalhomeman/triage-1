import numpy

import warnings

import pytest

from triage.component.catwalk.feature_importances import (
    _ad_hoc_feature_importances,
    get_feature_importances,
)

from sklearn import datasets
from sklearn.svm import SVC
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression

from sklearn.model_selection import train_test_split


@pytest.fixture
def trained_models():
    dataset = datasets.load_breast_cancer()
    X = dataset.data
    y = dataset.target

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=12345
    )

    rf = RandomForestClassifier()
    rf.fit(X_train, y_train)

    lr = LogisticRegression()
    lr.fit(X_train, y_train)

    svc_w_linear_kernel = SVC(kernel="linear")
    svc_w_linear_kernel.fit(X_train, y_train)

    svc_wo_linear_kernel = SVC()
    svc_wo_linear_kernel.fit(X_train, y_train)

    dummy = DummyClassifier()
    dummy.fit(X_train, y_train)

    return {
        "RF": rf,
        "LR": lr,
        "SVC_w_linear_kernel": svc_w_linear_kernel,
        "Dummy": dummy,
        "SVC_wo_linear_kernel": svc_wo_linear_kernel,
    }


def test_throwing_warning_if_lr(trained_models):
    with pytest.warns(UserWarning):
        get_feature_importances(trained_models["LR"])


def test_throwing_warning_if_dummyclassifier(trained_models):
    with pytest.warns(UserWarning):
        get_feature_importances(trained_models["Dummy"])


def test_throwing_warning_if_SVC_wo_linear_kernel(trained_models):
    with pytest.warns(UserWarning):
        get_feature_importances(trained_models["SVC_wo_linear_kernel"])


def test_correct_feature_importances_for_lr(trained_models):
    feature_importances = get_feature_importances(trained_models["LR"])

    ## It returns the intercept, too
    assert feature_importances.shape == (30,)


def test_correct_feature_importances_for_rf(trained_models):
    feature_importances = get_feature_importances(trained_models["RF"])
    assert feature_importances.shape == (30,)


def test_correct_feature_importances_for_svc_w_linear_kernel(trained_models):
    feature_importances = get_feature_importances(trained_models["SVC_w_linear_kernel"])
    assert feature_importances.shape == (30,)


def test_correct_feature_importances_for_svc_wo_linear_kernel(trained_models):
    feature_importances = get_feature_importances(
        trained_models["SVC_wo_linear_kernel"]
    )
    assert feature_importances is None


def test_correct_feature_importances_for_dummy(trained_models):
    feature_importances = get_feature_importances(trained_models["Dummy"])
    assert feature_importances is None
