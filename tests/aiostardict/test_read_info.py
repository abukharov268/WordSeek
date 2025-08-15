"""Tests for stardict_importer module"""

from anyio import AsyncFile
from pytest_mock import MockerFixture
from aiostardict import read_info, StarDictInfo


async def test_read_info(mocker: MockerFixture):
    """Test reading of base info about StarDict dictionary."""

    data = [
        "StarDict's dict ifo file\n",
        "version=3.0.0\n",
        "bookname=dict name\n",
        "wordcount=2\n",
        "idxfilesize=33\n",
        "idxoffsetbits=32",
    ]
    data_iter = iter(data)

    mock_file = mocker.MagicMock(AsyncFile, name="ifo file mock")
    mock_file.readline.side_effect = data_iter
    mock_file.readlines.return_value = data_iter
    mock_file.__aenter__.return_value = mock_file
    mock_file.__aexit__.called
    open_mock = mocker.patch("anyio.open_file", return_value=mock_file)

    result = await read_info("my-file.ifo")

    open_mock.assert_called_once()
    assert open_mock.call_args.args == ("my-file.ifo", "r")
    assert result == StarDictInfo("3.0.0", "dict name", 2, 33, 32)
