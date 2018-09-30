# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import errno
import stat
import unittest
from unittest import mock

from iotedgehubdev.utils import Utils


class TestUtilAPIs(unittest.TestCase):
    @mock.patch('shutil.rmtree')
    @mock.patch('os.path.exists')
    def test_delete_dir_when_dir_exists(self, mock_exists, mock_rmtree):
        """ Test a valid invocation of API delete_dir when dir to be deleted exists"""
        # arrange
        dir_path = 'blah'
        mock_exists.return_value = True

        # act
        Utils.delete_dir(dir_path)

        # assert
        mock_exists.assert_called_with(dir_path)
        mock_rmtree.assert_called_with(dir_path, onerror=Utils._remove_readonly_callback)

    @mock.patch('os.unlink')
    @mock.patch('os.chmod')
    def test_delete_dir_execute_onerror_callback(self, mock_chmod, mock_unlink):
        """ Test rmtree onerror callback invocation"""
        # arrange
        dir_path = 'blah'
        ignored = 0

        # act
        Utils._remove_readonly_callback(ignored, dir_path, ignored)

        # assert
        mock_chmod.assert_called_with(dir_path, stat.S_IWRITE)
        mock_unlink.assert_called_with(dir_path)

    @mock.patch('shutil.rmtree')
    @mock.patch('os.path.exists')
    def test_delete_dir_when_dir_does_not_exist(self, mock_exists, mock_rmtree):
        """ Test a valid invocation of API delete_dir when dir to be deleted does not exist"""
        # arrange
        dir_path = 'blah'
        mock_exists.return_value = False

        # act
        Utils.delete_dir(dir_path)

        # assert
        mock_exists.assert_called_with(dir_path)
        mock_rmtree.assert_not_called()

    @mock.patch('shutil.rmtree')
    @mock.patch('os.path.exists')
    def test_delete_dir_raises_oserror_when_rmtree_fails(self, mock_exists, mock_rmtree):
        """ Tests invocation of API delete_dir raises OSError when rmtree raises OSError"""
        # arrange
        dir_path = 'blah'
        mock_exists.return_value = True
        mock_rmtree.side_effect = OSError('rmtree error')

        # act, assert
        with self.assertRaises(OSError):
            Utils.delete_dir(dir_path)

    @mock.patch('os.makedirs')
    def test_mkdir_if_needed_when_dir_does_not_exist(self, mock_mkdirs):
        """ Test a valid invocation of API mkdir_if_needed when dir to be made does not exist """
        # arrange
        dir_path = 'blah'

        # act
        Utils.mkdir_if_needed(dir_path)

        # assert
        mock_mkdirs.assert_called_with(dir_path)

    @mock.patch('os.makedirs')
    def test_mkdir_if_needed_when_dir_exists(self, mock_mkdirs):
        """ Test a valid invocation of API mkdir_if_needed when dir to be made already exists """
        # arrange
        dir_path = 'blah'
        mock_mkdirs.side_effect = OSError(errno.EEXIST, 'Directory exists.')

        # act
        Utils.mkdir_if_needed(dir_path)

        # assert
        mock_mkdirs.assert_called_with(dir_path)

    @mock.patch('os.makedirs')
    def test_mkdir_if_needed_raises_oserror_when_mkdir_fails(self, mock_mkdirs):
        """ Tests invocation of API mkdir_if_needed raises OSError when makedirs raises OSError"""
        # arrange
        dir_path = 'blah'
        mock_mkdirs.side_effect = OSError(errno.EACCES, 'Directory permission error')

        # act, assert
        with self.assertRaises(OSError):
            Utils.mkdir_if_needed(dir_path)

    @mock.patch('os.path.isfile')
    @mock.patch('os.path.exists')
    def test_check_if_file_exists_returns_true(self, mock_exists, mock_isfile):
        """ Test a valid invocation of API check_if_file_exists """
        # arrange #1
        file_path = 'blah'
        mock_exists.return_value = True
        mock_isfile.return_value = True

        # act
        result = Utils.check_if_file_exists(file_path)

        # assert
        mock_exists.assert_called_with(file_path)
        mock_isfile.assert_called_with(file_path)
        self.assertTrue(result)

    @mock.patch('os.path.isfile')
    @mock.patch('os.path.exists')
    def test_check_if_file_exists_returns_false_if_exists_returns_false(self,
                                                                        mock_exists, mock_isfile):
        """ Test a valid invocation of API check_if_file_exists """

        # arrange
        file_path = 'blah'
        mock_exists.return_value = False

        # act
        result = Utils.check_if_file_exists(file_path)

        # assert
        mock_exists.assert_called_with(file_path)
        mock_isfile.assert_not_called()
        self.assertFalse(result)

    @mock.patch('os.path.isfile')
    @mock.patch('os.path.exists')
    def test_check_if_file_exists_returns_false_if_isfile_returns_false(self,
                                                                        mock_exists, mock_isfile):
        """ Test a valid invocation of API check_if_file_exists """

        # arrange
        file_path = 'blah'
        mock_exists.return_value = True
        mock_isfile.return_value = False

        # act
        result = Utils.check_if_file_exists(file_path)

        # assert
        mock_exists.assert_called_with(file_path)
        mock_isfile.assert_called_with(file_path)
        self.assertFalse(result)

    @mock.patch('os.path.isfile')
    @mock.patch('os.path.exists')
    def test_check_if_file_exists_returns_false_path_is_none(self, mock_exists, mock_isfile):
        """ Test a valid invocation of API check_if_file_exists """

        # arrange
        file_path = None

        # act
        result = Utils.check_if_file_exists(file_path)

        # assert
        mock_exists.assert_not_called()
        mock_isfile.assert_not_called()
        self.assertFalse(result)

    @mock.patch('os.path.isdir')
    @mock.patch('os.path.exists')
    def test_check_if_dir_exists_returns_true(self, mock_exists, mock_isdir):
        # arrange #1
        dir_path = 'blah'
        mock_exists.return_value = True
        mock_isdir.return_value = True

        # act
        result = Utils.check_if_directory_exists(dir_path)

        # assert
        mock_exists.assert_called_with(dir_path)
        mock_isdir.assert_called_with(dir_path)
        self.assertTrue(result)

    @mock.patch('os.path.isdir')
    @mock.patch('os.path.exists')
    def test_check_if_dir_exists_returns_false_if_exists_returns_false(self,
                                                                       mock_exists, mock_isdir):
        # arrange
        dir_path = 'blah'
        mock_exists.return_value = False

        # act
        result = Utils.check_if_directory_exists(dir_path)

        # assert
        mock_exists.assert_called_with(dir_path)
        mock_isdir.assert_not_called()
        self.assertFalse(result)

    @mock.patch('os.path.isdir')
    @mock.patch('os.path.exists')
    def test_check_if_dir_exists_returns_false_if_isdir_returns_false(self,
                                                                      mock_exists, mock_isdir):
        # arrange
        dir_path = 'blah'
        mock_exists.return_value = True
        mock_isdir.return_value = False

        # act
        result = Utils.check_if_directory_exists(dir_path)

        # assert
        mock_exists.assert_called_with(dir_path)
        mock_isdir.assert_called_with(dir_path)
        self.assertFalse(result)

    @mock.patch('os.path.isdir')
    @mock.patch('os.path.exists')
    def test_check_if_dir_exists_returns_false_path_is_none(self, mock_exists, mock_isdir):
        # arrange
        dir_path = None

        # act
        result = Utils.check_if_directory_exists(dir_path)

        # assert
        mock_exists.assert_not_called()
        mock_isdir.assert_not_called()
        self.assertFalse(result)

    @mock.patch('socket.getfqdn')
    def test_get_hostname_valid(self, mock_hostname):
        """ Test a valid invocation of API get_hostname """
        # arrange
        hostname = 'test_hostname'
        mock_hostname.return_value = hostname
        # act
        result = Utils.get_hostname()

        # assert
        mock_hostname.assert_called_with()
        self.assertEqual(hostname, result)

    @mock.patch('socket.getfqdn')
    def test_get_hostname_raises_ioerror_when_getfqdn_raises_ioerror(self, mock_hostname):
        """ Tests invocation of API get_hostname raises IOError when getfqdn raises IOError"""
        # arrange
        mock_hostname.side_effect = IOError('getfqdn IO error')

        # act, assert
        with self.assertRaises(IOError):
            Utils.get_hostname()

    def test_get_sha256_hash(self):
        val = 'foo'

        assert Utils.get_sha256_hash(val) == '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'

    def test_hash_connection_str_hostname(self):
        connection_str = "HostName=ChaoyiTestIoT.azure-devices.net;DeviceId=edge-device;SharedAccessKey=foobarbazqux="

        assert Utils.hash_connection_str_hostname(connection_str) == (
            '6b8fcfea09003d5f104771e83bd9ff54c592ec2277ec1815df91dd64d1633778', 'azure-devices.net')
