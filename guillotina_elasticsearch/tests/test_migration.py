from guillotina.component import getUtility
from guillotina.interfaces import ICatalogUtility
from guillotina_elasticsearch.migration import Migrator
from guillotina_elasticsearch.tests.utils import add_content
from guillotina_elasticsearch.tests.utils import setup_txn_on_container

import asyncio
import json
import time


async def test_migrate_while_content_getting_added(es_requester):
    async with await es_requester as requester:
        await add_content(requester)

        container, request, txn, tm = await setup_txn_on_container(requester)

        search = getUtility(ICatalogUtility)
        await search.refresh(container)

        current_count = await search.get_doc_count(container)
        import pdb; pdb.set_trace()

        migrator = Migrator(search, container)
        add_content_task = asyncio.ensure_future(add_content(requester, base_id='foo-'))
        reindex_task = asyncio.ensure_future(migrator.run_migration())

        await asyncio.wait([reindex_task, add_content_task])
        await search.refresh(container)
        import pdb; pdb.set_trace()

        current_count = await search.get_doc_count(container)
        import pdb; pdb.set_trace()

        foo = 5

        await tm.abort(txn=txn)


async def test_migrate_get_all_uids(es_requester):
    async with await es_requester as requester:
        await add_content(requester)

        container, request, txn, tm = await setup_txn_on_container(requester)

        search = getUtility(ICatalogUtility)
        await search.refresh(container)

        current_count = await search.get_doc_count(container)

        migrator = Migrator(search, container)
        uids = await migrator.get_all_uids()

        assert len(uids) == current_count

        await tm.abort(txn=txn)


async def test_removes_orphans():
    pass


async def test_fixes_missing():
    pass


async def test_updates_changed_mapping_fields():
    pass


async def test_updates_index_name(es_requester):
    async with await es_requester as requester:
        container, request, txn, tm = await setup_txn_on_container(requester)
        search = getUtility(ICatalogUtility)
        existing_index = await search.get_real_index_name(container)
        assert search.conn.indices.exists(existing_index)
        migrator = Migrator(search, container)
        await migrator.run_migration()
        assert not search.conn.indices.exists(existing_index)
        assert search.conn.indices.exists(migrator.next_index_name)