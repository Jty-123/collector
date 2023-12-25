#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Huawei Technologies Co., Ltd.
# A-Tune is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2019-10-29

"""
The sub class of the monitor, used to collect the system load average statistics.
"""
import inspect
import logging
import subprocess
import getopt
import re
from ..common import Monitor

LOGGER = logging.getLogger(__name__)


class SysLdavg(Monitor):
    """To collect the system load average statistics"""
    _module = "SYS"
    _purpose = "LDAVG"
    _option = "-q {int} 1"

    def __init__(self, user=None):
        Monitor.__init__(self, user)
        self.__cmd = "sar"
        self.__interval = 1
        self.decode.__func__.__doc__ = Monitor.decode.__doc__ % (
            "--fields=time/runq-sz/plist-sz/ldavg-1/ldavg-5/ldavg-15/blocked/task-util")

    def _get(self, para=None):
        if para is not None:
            opts, _ = getopt.getopt(para.split(), None, ['interval='])
            for opt, val in opts:
                if opt in '--interval':
                    if val.isdigit():
                        self.__interval = int(val)
                    else:
                        err = ValueError(
                            "Invalid parameter: {opt}={val}".format(
                                opt=opt, val=val))
                        LOGGER.error("%s.%s: %s", self.__class__.__name__,
                                     inspect.stack()[0][3], str(err))
                        raise err
                    continue

        output = subprocess.check_output(
            "{cmd} {opt}".format(
                cmd=self.__cmd,
                opt=self._option.format(
                    int=self.__interval)).split())
        return output.decode()

    def decode(self, info, para):
        """
        decode the result of the operation
        :param info:  content that needs to be decoded
        :param para:  command line argument
        :returns ret:  operation result
        """
        if para is None:
            return info

        keyword = {"time": 0,
                   "runq-sz": 1,
                   "plist-sz": 2,
                   "ldavg-1": 3,
                   "ldavg-5": 4,
                   "ldavg-15": 5,
                   "blocked": 6,
                   "task-util": "task-util"}

        keys = []
        ret = ""

        opts, _ = getopt.getopt(para.split(), None, ['nic=', 'fields=', 'device='])
        for opt, val in opts:
            if opt in '--fields':
                keys.append(keyword[val])
                continue

        pattern = re.compile(
            r"^(\d.*?)\ {1,}(\d*)\ {1,}(\d*)\ {1,}(\d*\.?\d*)\ {1,}(\d*\.?\d*)\ {1,}(\d*\.?\d*)"
            r"\ {1,}(\d*)",
            re.UNICODE | re.MULTILINE)
        search_obj = pattern.findall(info)
        if len(search_obj) == 0:
            err = LookupError("Fail to find data")
            LOGGER.error("%s.%s: %s", self.__class__.__name__,
                         inspect.stack()[0][3], str(err))
            raise err

        for i in keys:
            if type(i).__name__ == 'int':
                ret = ret + " " + search_obj[-1][i]
            elif i == "task-util":
                with open("/proc/sys/kernel/threads-max", 'r') as file:
                    threads_max = file.read()
                util = int(search_obj[-1][keyword["plist-sz"]]) / \
                    int(threads_max) * 100
                ret = ret + " " + str(util)
        return ret
