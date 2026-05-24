from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime
from typing import Any

from bson import ObjectId


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, modified_count: int = 0) -> None:
        self.modified_count = modified_count


def _field_matches(doc_value: Any, condition: Any) -> bool:
    if isinstance(condition, dict):
        if "$gte" in condition:
            if doc_value is None:
                return False
            return doc_value >= condition["$gte"]
        if "$gt" in condition:
            if doc_value is None:
                return False
            return doc_value > condition["$gt"]
        if "$ne" in condition:
            return doc_value != condition["$ne"]
        if "$in" in condition:
            return doc_value in condition["$in"]
        if "$regex" in condition:
            if doc_value is None:
                return False
            pattern = condition["$regex"]
            flags = 0
            if "$options" in condition:
                if "i" in condition["$options"]:
                    flags |= re.IGNORECASE
            return bool(re.search(pattern, str(doc_value), flags))
        return False
    if condition is None:
        return doc_value is None
    return doc_value == condition


def _doc_matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        if key == "$or":
            if not isinstance(expected, list):
                return False
            if not any(_doc_matches(doc, sub_query) for sub_query in expected):
                return False
        else:
            if not _field_matches(doc.get(key), expected):
                return False
    return True


class MockCursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.docs = docs

    def sort(self, *args, **kwargs) -> MockCursor:
        return self

    def skip(self, *args, **kwargs) -> MockCursor:
        return self

    def limit(self, *args, **kwargs) -> MockCursor:
        return self

    async def to_list(self, length: int) -> list[dict[str, Any]]:
        return deepcopy(self.docs[:length])


class MockCollection:
    def __init__(self) -> None:
        self.docs: list[dict[str, Any]] = []

    async def find_one(
        self,
        query: dict[str, Any],
        sort: list[tuple[str, int]] | None = None,
    ) -> dict[str, Any] | None:
        matches = [doc for doc in self.docs if _doc_matches(doc, query)]
        if not matches:
            return None
        if sort:
            field, direction = sort[0]
            matches.sort(
                key=lambda d: d.get(field) or datetime.min,
                reverse=direction == -1,
            )
        return deepcopy(matches[0])

    def find(self, query: dict[str, Any] | None = None) -> MockCursor:
        if query is None:
            query = {}
        matches = [doc for doc in self.docs if _doc_matches(doc, query)]
        return MockCursor(matches)

    async def find_one_and_update(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
        return_document: bool = False,
    ) -> dict[str, Any] | None:
        found_doc = None
        for doc in self.docs:
            if _doc_matches(doc, query):
                found_doc = doc
                break

        if not found_doc:
            if upsert:
                new_doc = deepcopy(query)
                if "_id" not in new_doc:
                    new_doc["_id"] = ObjectId()
                self.docs.append(new_doc)
                found_doc = new_doc
            else:
                return None

        if "$set" in update:
            found_doc.update(update["$set"])
        if "$inc" in update:
            for field, val in update["$inc"].items():
                found_doc[field] = found_doc.get(field, 0) + val

        return deepcopy(found_doc)

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        doc = deepcopy(document)
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.docs.append(doc)
        return InsertOneResult(doc["_id"])

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> UpdateResult:
        modified = 0
        for doc in self.docs:
            if _doc_matches(doc, query):
                if "$set" in update:
                    doc.update(update["$set"])
                    modified += 1
                break
        return UpdateResult(modified)

    async def update_many(self, query: dict[str, Any], update: dict[str, Any]) -> UpdateResult:
        modified = 0
        for doc in self.docs:
            if _doc_matches(doc, query) and "$set" in update:
                doc.update(update["$set"])
                modified += 1
        return UpdateResult(modified)

    async def delete_many(self, query: dict[str, Any]) -> UpdateResult:
        before = len(self.docs)
        self.docs = [doc for doc in self.docs if not _doc_matches(doc, query)]
        return UpdateResult(before - len(self.docs))

    async def count_documents(self, query: dict[str, Any]) -> int:
        return sum(1 for doc in self.docs if _doc_matches(doc, query))


class MockDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, MockCollection] = {}

    def __getitem__(self, name: str) -> MockCollection:
        if name not in self._collections:
            self._collections[name] = MockCollection()
        return self._collections[name]

    def clear(self) -> None:
        self._collections.clear()
