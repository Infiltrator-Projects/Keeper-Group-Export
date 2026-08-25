"""Pure regression tests for application-local helpers."""

import unittest
from types import SimpleNamespace

from keeper_group_export.common import build_folder_record_index, safe_filename


class SafeFilenameTests(unittest.TestCase):
    def test_replaces_windows_reserved_characters_and_collapses_space(self):
        self.assertEqual(
            safe_filename('Year 3 / Group: A  *  Credentials'),
            'Year 3 - Group- A - Credentials',
        )

    def test_empty_value_has_stable_fallback(self):
        self.assertEqual(safe_filename('   '), 'Keeper-Group')


class FolderRecordIndexTests(unittest.TestCase):
    def test_parent_contains_direct_and_descendant_records_without_duplicates(self):
        folders = {
            'root': SimpleNamespace(subfolders=['a', 'b']),
            'a': SimpleNamespace(subfolders=['leaf']),
            'b': SimpleNamespace(subfolders=[]),
            'leaf': SimpleNamespace(subfolders=[]),
        }
        direct = {
            'root': {'r0'},
            'a': {'r1', 'shared'},
            'b': {'r2', 'shared'},
            'leaf': {'r3'},
        }

        index = build_folder_record_index(folders, direct)

        self.assertEqual(index['leaf'], frozenset({'r3'}))
        self.assertEqual(index['a'], frozenset({'r1', 'shared', 'r3'}))
        self.assertEqual(index['b'], frozenset({'r2', 'shared'}))
        self.assertEqual(
            index['root'],
            frozenset({'r0', 'r1', 'r2', 'r3', 'shared'}),
        )

    def test_malformed_cycle_is_bounded(self):
        folders = {
            'a': SimpleNamespace(subfolders=['b']),
            'b': SimpleNamespace(subfolders=['a']),
        }
        direct = {'a': {'ra'}, 'b': {'rb'}}

        index = build_folder_record_index(folders, direct)

        self.assertIn('ra', index['a'])
        self.assertIn('rb', index['a'])
        self.assertIn('rb', index['b'])


if __name__ == '__main__':
    unittest.main()
