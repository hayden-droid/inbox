#!/usr/bin/python3

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MeanShift
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from collections import Counter
from typing import List, Dict, NamedTuple

from .eml import Store, Message


class Group(NamedTuple):
    titles: Counter
    messages: List[Message]


def group_messages_by_sender(store: Store) -> Dict[str, Group]:
    groups: Dict[str, Group] = {}
    for msg in store.list_messages():
        k = msg.metadata.mail_from[1].rsplit('@', 1)[1]
        title = msg.metadata.mail_from[0] or k or 'None'
        group = groups.setdefault(k, Group(titles=Counter(), messages=[]))
        group.titles[title] += 1
        group.messages.append(msg)

    return groups


def group_messages(store: Store) -> Dict[str, Group]:
    documents, messages = zip(
        *[(msg.metadata.tokens, msg) for msg in store.list_messages()]
    )

    pipeline = Pipeline(
      steps=[
        ('tfidf', TfidfVectorizer()),
        ('trans', FunctionTransformer(
            lambda x: x.todense(), accept_sparse=True)),
        ('clust', MeanShift(bandwidth=0.99))
      ])

    pipeline.fit(documents)
    groups: Dict[str, Group] = {}
    for msg, label in zip(messages, pipeline.named_steps['clust'].labels_):
        group = groups.setdefault(label, Group(titles=Counter(), messages=[]))
        metadata = msg.metadata
        group.titles[metadata.mail_from[0] or metadata.mail_from[1]] += 1
        group.messages.append(msg)

    return groups