"""Exercise separate inventories without changing project assets (standard library)."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_gallery
import validate_gallery
from gallery_data import ROOT, libraries


class MultiMechTests(unittest.TestCase):
    def test_empty_then_populated_second_library(self):
        catalog = copy.deepcopy(libraries())
        hellcat, first = catalog[0]
        sherman, second = catalog[1]
        # Identical slug and number deliberately exercise per-mech isolation.
        first['clips'] = first['clips'][:1]
        first['gallery_groups'] = first['gallery_groups'][:1]
        second['clips'] = []
        second['gallery_groups'] = []
        # Keep any further registered libraries in the fixture and exercise their
        # navigation/isolation too, without requiring all of their real assets.
        for _, data in catalog[2:]:
            data['clips'] = []
            data['gallery_groups'] = []
        with tempfile.TemporaryDirectory(prefix='mech-gallery-test-') as temp:
            root = Path(temp)
            shutil.copytree(ROOT / 'templates', root / 'templates')
            shutil.copytree(ROOT / 'styles', root / 'styles')
            for mech, data in catalog:
                for key in ['manifest', 'contact_sheet', 'guide']:
                    if key in mech:
                        file = root / mech[key]
                        file.parent.mkdir(parents=True, exist_ok=True)
                        file.write_text('fixture', encoding='utf-8')
                (root / mech['animation_dir']).mkdir(parents=True, exist_ok=True)
            (root / 'docs/adding-a-mech.md').write_text('fixture', encoding='utf-8')
            gif = first['clips'][0]['slug'] + '.gif'
            shutil.copyfile(ROOT / hellcat['animation_dir'] / gif,
                            root / hellcat['animation_dir'] / gif)
            with patch.object(build_gallery, 'ROOT', root), patch.object(validate_gallery, 'ROOT', root):
                for mech, data in catalog:
                    build_gallery.build(mech, data, catalog)
                for mech, data in catalog:
                    validate_gallery.validate_library(mech, data, catalog)
                page = (root / sherman['page']).read_text(encoding='utf-8')
                self.assertIn('No animation previews yet', page)
                self.assertNotIn('Contact sheet</a>', page)
                self.assertNotIn('Weapon aiming:', page)

                second['clips'] = copy.deepcopy(first['clips'])
                second['gallery_groups'] = copy.deepcopy(first['gallery_groups'])
                second['clips'][0]['action'] = 'TEST SHERMAN ACTION'
                shutil.copyfile(root / hellcat['animation_dir'] / gif,
                                root / sherman['animation_dir'] / gif)
                for mech, data in catalog:
                    build_gallery.build(mech, data, catalog)
                for mech, data in catalog:
                    validate_gallery.validate_library(mech, data, catalog)
                page = (root / sherman['page']).read_text(encoding='utf-8')
                self.assertIn('TEST SHERMAN ACTION', page)
                self.assertNotIn('No animation previews yet', page)
                self.assertNotIn('TEST SHERMAN ACTION', (root / hellcat['page']).read_text(encoding='utf-8'))

                for extra, inventory in catalog[2:]:
                    inventory['clips'] = copy.deepcopy(first['clips'])
                    inventory['gallery_groups'] = copy.deepcopy(first['gallery_groups'])
                    inventory['clips'][0]['action'] = 'TEST ' + extra['id']
                    shutil.copyfile(root / hellcat['animation_dir'] / gif,
                                    root / extra['animation_dir'] / gif)
                for mech, data in catalog:
                    build_gallery.build(mech, data, catalog)
                    validate_gallery.validate_library(mech, data, catalog)
                    page = (root / mech['page']).read_text(encoding='utf-8')
                    self.assertIn(data['clips'][0]['action'], page)
                    for other, inventory in catalog:
                        if other['id'] != mech['id']:
                            self.assertNotIn(inventory['clips'][0]['action'], page)

                second['clips'][0]['label'] = '02 Walk'
                with self.assertRaisesRegex(ValueError, 'numbering has gaps'):
                    validate_gallery.validate_library(sherman, second, catalog)


if __name__ == '__main__':
    unittest.main()
