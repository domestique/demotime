from demotime import models
from demotime.tests import BaseTestCase


class TestSettingModels(BaseTestCase):

    def _create_setting(self, raw_value, setting_type, active=True):
        return models.Setting.create_setting(
            title='Testing',
            key='testing',
            raw_value=raw_value,
            setting_type=setting_type,
            active=active
        )

    def test_setting__str__(self):
        setting = self._create_setting('test', models.Setting.STRING)
        self.assertEqual(setting.__str__(), 'Setting: {}'.format(setting.title))

    def test_dict_setting(self):
        setting = self._create_setting(
            '{"test": [1, 2, 3], "wut": "oh yeah"}',
            models.Setting.DICT
        )
        self.assertEqual(setting.value, {
            'test': [1, 2, 3],
            'wut': 'oh yeah'
        })

    def test_list_setting(self):
        setting = self._create_setting(
            '[1, "2", 3]',
            models.Setting.LIST
        )
        self.assertEqual(setting.value, (1, '2', 3))

        setting.raw_value = "1, 2, 3"
        self.assertEqual(setting.value, ('1', '2', '3'))

    def test_bool_setting(self):
        setting = self._create_setting('true', models.Setting.BOOL)
        self.assertEqual(setting.value, True)

        setting.raw_value = 't'
        self.assertEqual(setting.value, True)

        setting.raw_value = '1'
        self.assertEqual(setting.value, True)

        setting.raw_value = 'f'
        self.assertEqual(setting.value, False)

    def test_int_setting(self):
        setting = self._create_setting('1', models.Setting.INT)
        self.assertEqual(setting.value, 1)

    def test_string_setting(self):
        setting = self._create_setting('testing', models.Setting.STRING)
        self.assertEqual(setting.value, 'testing')


class TestSettingManager(BaseTestCase):

    def setUp(self):
        super(TestSettingManager, self).setUp()
        self.setting = models.Setting.create_setting(
            title='Testing',
            key='testing',
            description='testing',
            raw_value='1',
            setting_type=models.Setting.STRING,
            active=True
        )

    def test_get_value_missing_setting(self):
        value = models.Setting.objects.get_value('testing-bad')
        self.assertIsNone(value)

    def test_get_value_missing_setting_default(self):
        value = models.Setting.objects.get_value('testing-bad', default='default')
        self.assertEqual(value, 'default')

    def test_get_value_inactive_setting_no_default(self):
        self.setting.active = False
        self.setting.save(update_fields=['active'])
        value = models.Setting.objects.get_value('testing')
        self.assertIsNone(value)

    def test_get_value_inactive_setting_default(self):
        self.setting.active = False
        self.setting.save(update_fields=['active'])
        value = models.Setting.objects.get_value('testing', default='default')
        self.assertEqual(value, 'default')

    def test_get_value_success(self):
        value = models.Setting.objects.get_value('testing')
        self.assertEqual(value, '1')
