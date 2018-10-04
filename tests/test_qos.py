import unittest
import pdb
import argparse
import test_inc
import json

PATH_SET_SONIC_TMPL = '/sonic'
PATH_GET_SONIC_TMPL = '/sonic'
TEST_CFG_QOS_JSON   = """
{
    "TC_TO_PRIORITY_GROUP_MAP": {
        "AZURE": {
            "0": "0",
            "1": "1",
            "2": "2",
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
            "7": "7"
        }
    },
    "MAP_PFC_PRIORITY_TO_QUEUE": {
        "AZURE": {
            "0": "0",
            "1": "1",
            "2": "2",
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
            "7": "7"
        }
    },
    "TC_TO_QUEUE_MAP": {
        "AZURE": {
            "0": "0",
            "1": "1",
            "2": "2",
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
            "7": "7"
        }
    },
    "DSCP_TO_TC_MAP": {
        "AZURE": {
            "0":"0",
            "1":"0",
            "2":"0",
            "3":"3",
            "4":"4",
            "5":"0",
            "6":"0",
            "7":"0",
            "8":"1",
            "9":"0",
            "10":"0",
            "11":"0",
            "12":"0",
            "13":"0",
            "14":"0",
            "15":"0",
            "16":"0",
            "17":"0",
            "18":"0",
            "19":"0",
            "20":"0",
            "21":"0",
            "22":"0",
            "23":"0",
            "24":"0",
            "25":"0",
            "26":"0",
            "27":"0",
            "28":"0",
            "29":"0",
            "30":"0",
            "31":"0",
            "32":"0",
            "33":"0",
            "34":"0",
            "35":"0",
            "36":"0",
            "37":"0",
            "38":"0",
            "39":"0",
            "40":"0",
            "41":"0",
            "42":"0",
            "43":"0",
            "44":"0",
            "45":"0",
            "46":"0",
            "47":"0",
            "48":"0",
            "49":"0",
            "50":"0",
            "51":"0",
            "52":"0",
            "53":"0",
            "54":"0",
            "55":"0",
            "56":"0",
            "57":"0",
            "58":"0",
            "59":"0",
            "60":"0",
            "61":"0",
            "62":"0",
            "63":"0"
        }
    },
    "SCHEDULER": {
        "scheduler.0" : {
            "type":"DWRR",
            "weight": "25"
        },
        "scheduler.1" : {
            "type":"DWRR",
            "weight": "30"
        },
        "scheduler.2" : {
            "type":"DWRR",
            "weight": "20"
        }
    },
    "PORT_QOS_MAP": {
        "Ethernet0,Ethernet1,Ethernet4,Ethernet5,Ethernet6,Ethernet7,Ethernet8,Ethernet9,Ethernet10,Ethernet11,Ethernet12,Ethernet13,Ethernet14,Ethernet15,Ethernet16,Ethernet17,Ethernet20,Ethernet21,Ethernet22,Ethernet23,Ethernet24,Ethernet25,Ethernet26,Ethernet27,Ethernet28,Ethernet29,Ethernet30,Ethernet31,Ethernet32,Ethernet36,Ethernet37,Ethernet38,Ethernet39,Ethernet40,Ethernet41,Ethernet42,Ethernet48,Ethernet52,Ethernet53,Ethernet54,Ethernet55,Ethernet56,Ethernet57,Ethernet58": {
            "dscp_to_tc_map"  : "[DSCP_TO_TC_MAP|AZURE]",
            "tc_to_queue_map" : "[TC_TO_QUEUE_MAP|AZURE]",
            "tc_to_pg_map"    : "[TC_TO_PRIORITY_GROUP_MAP|AZURE]",
            "pfc_to_queue_map": "[MAP_PFC_PRIORITY_TO_QUEUE|AZURE]",
            "pfc_enable": "3,4"
        }
    },
    "WRED_PROFILE": {
        "AZURE_LOSSLESS" : {
            "wred_green_enable":"true",
            "wred_yellow_enable":"true",
            "wred_red_enable":"true",
            "ecn":"ecn_all",
            "red_max_threshold":"312000",
            "red_min_threshold":"104000",
            "yellow_max_threshold":"312000",
            "yellow_min_threshold":"104000",
            "green_max_threshold": "312000",
            "green_min_threshold": "104000"
        }
    },
    "QUEUE": {
        "Ethernet0,Ethernet1,Ethernet4,Ethernet5,Ethernet6,Ethernet7,Ethernet8,Ethernet9,Ethernet10,Ethernet11,Ethernet12,Ethernet13,Ethernet14,Ethernet15,Ethernet16,Ethernet17,Ethernet20,Ethernet21,Ethernet22,Ethernet23,Ethernet24,Ethernet25,Ethernet26,Ethernet27,Ethernet28,Ethernet29,Ethernet30,Ethernet31,Ethernet32,Ethernet36,Ethernet37,Ethernet38,Ethernet39,Ethernet40,Ethernet41,Ethernet42,Ethernet48,Ethernet52,Ethernet53,Ethernet54,Ethernet55,Ethernet56,Ethernet57,Ethernet58|3-4" : {
            "scheduler"     :   "[SCHEDULER|scheduler.0]",
            "wred_profile"  :   "[WRED_PROFILE|AZURE_LOSSLESS]"
        },
        "Ethernet0,Ethernet1,Ethernet4,Ethernet5,Ethernet6,Ethernet7,Ethernet8,Ethernet9,Ethernet10,Ethernet11,Ethernet12,Ethernet13,Ethernet14,Ethernet15,Ethernet16,Ethernet17,Ethernet20,Ethernet21,Ethernet22,Ethernet23,Ethernet24,Ethernet25,Ethernet26,Ethernet27,Ethernet28,Ethernet29,Ethernet30,Ethernet31,Ethernet32,Ethernet36,Ethernet37,Ethernet38,Ethernet39,Ethernet40,Ethernet41,Ethernet42,Ethernet48,Ethernet52,Ethernet53,Ethernet54,Ethernet55,Ethernet56,Ethernet57,Ethernet58|0" : {
            "scheduler"     :   "[SCHEDULER|scheduler.1]"
        },
        "Ethernet0,Ethernet1,Ethernet4,Ethernet5,Ethernet6,Ethernet7,Ethernet8,Ethernet9,Ethernet10,Ethernet11,Ethernet12,Ethernet13,Ethernet14,Ethernet15,Ethernet16,Ethernet17,Ethernet20,Ethernet21,Ethernet22,Ethernet23,Ethernet24,Ethernet25,Ethernet26,Ethernet27,Ethernet28,Ethernet29,Ethernet30,Ethernet31,Ethernet32,Ethernet36,Ethernet37,Ethernet38,Ethernet39,Ethernet40,Ethernet41,Ethernet42,Ethernet48,Ethernet52,Ethernet53,Ethernet54,Ethernet55,Ethernet56,Ethernet57,Ethernet58|1" : {
            "scheduler"     :   "[SCHEDULER|scheduler.2]"
        }
    }
}"""

TEST_CLR_QOS_JSON   = """
{
    "TC_TO_PRIORITY_GROUP_MAP": {
        "AZURE": null
    },
    "MAP_PFC_PRIORITY_TO_QUEUE": {
        "AZURE": null
    },
    "TC_TO_QUEUE_MAP": {
        "AZURE": null
    },
    "DSCP_TO_TC_MAP": {
        "AZURE": null
    },
    "SCHEDULER": {
        "scheduler.0" : null,
        "scheduler.1" : null,
        "scheduler.2" : null
    },
    "PORT_QOS_MAP": {
        "Ethernet0,Ethernet1,Ethernet4,Ethernet5,Ethernet6,Ethernet7,Ethernet8,Ethernet9,Ethernet10,Ethernet11,Ethernet12,Ethernet13,Ethernet14,Ethernet15,Ethernet16,Ethernet17,Ethernet20,Ethernet21,Ethernet22,Ethernet23,Ethernet24,Ethernet25,Ethernet26,Ethernet27,Ethernet28,Ethernet29,Ethernet30,Ethernet31,Ethernet32,Ethernet36,Ethernet37,Ethernet38,Ethernet39,Ethernet40,Ethernet41,Ethernet42,Ethernet48,Ethernet52,Ethernet53,Ethernet54,Ethernet55,Ethernet56,Ethernet57,Ethernet58": null
    },
    "WRED_PROFILE": {
        "AZURE_LOSSLESS" : null
    },
    "QUEUE": {
        "Ethernet0,Ethernet1,Ethernet4,Ethernet5,Ethernet6,Ethernet7,Ethernet8,Ethernet9,Ethernet10,Ethernet11,Ethernet12,Ethernet13,Ethernet14,Ethernet15,Ethernet16,Ethernet17,Ethernet20,Ethernet21,Ethernet22,Ethernet23,Ethernet24,Ethernet25,Ethernet26,Ethernet27,Ethernet28,Ethernet29,Ethernet30,Ethernet31,Ethernet32,Ethernet36,Ethernet37,Ethernet38,Ethernet39,Ethernet40,Ethernet41,Ethernet42,Ethernet48,Ethernet52,Ethernet53,Ethernet54,Ethernet55,Ethernet56,Ethernet57,Ethernet58|3-4" : null,
        "Ethernet0,Ethernet1,Ethernet4,Ethernet5,Ethernet6,Ethernet7,Ethernet8,Ethernet9,Ethernet10,Ethernet11,Ethernet12,Ethernet13,Ethernet14,Ethernet15,Ethernet16,Ethernet17,Ethernet20,Ethernet21,Ethernet22,Ethernet23,Ethernet24,Ethernet25,Ethernet26,Ethernet27,Ethernet28,Ethernet29,Ethernet30,Ethernet31,Ethernet32,Ethernet36,Ethernet37,Ethernet38,Ethernet39,Ethernet40,Ethernet41,Ethernet42,Ethernet48,Ethernet52,Ethernet53,Ethernet54,Ethernet55,Ethernet56,Ethernet57,Ethernet58|0" : null,
        "Ethernet0,Ethernet1,Ethernet4,Ethernet5,Ethernet6,Ethernet7,Ethernet8,Ethernet9,Ethernet10,Ethernet11,Ethernet12,Ethernet13,Ethernet14,Ethernet15,Ethernet16,Ethernet17,Ethernet20,Ethernet21,Ethernet22,Ethernet23,Ethernet24,Ethernet25,Ethernet26,Ethernet27,Ethernet28,Ethernet29,Ethernet30,Ethernet31,Ethernet32,Ethernet36,Ethernet37,Ethernet38,Ethernet39,Ethernet40,Ethernet41,Ethernet42,Ethernet48,Ethernet52,Ethernet53,Ethernet54,Ethernet55,Ethernet56,Ethernet57,Ethernet58|1" : null
    }
}"""

class TestQos(test_inc.MyTestCase):
    def chk_output(self, tbl, output, is_assert_in = True):
        if isinstance(tbl, dict):
            for key in tbl:
                self.chk_output(tbl[key], output, is_assert_in)
        else:
            chk_str = str(tbl)
            if is_assert_in:
                self.assertIn(chk_str, output)
            else:
                self.assertNotIn(chk_str, output)

    def test_set_sonic_qos_cfg(self):
        org_cfg = eval(TEST_CFG_QOS_JSON)
        output = self.run_script(['update', PATH_SET_SONIC_TMPL, "'{0}'".format(TEST_CFG_QOS_JSON)])
        output = self.run_script(['get', PATH_GET_SONIC_TMPL, ''])
        output = "".join(output.replace('\n', '').split())
        self.chk_output(org_cfg, output)

    def test_clear_sonic_qos_cfg(self):
        org_cfg = eval(TEST_CFG_QOS_JSON)
        output = self.run_script(['update', PATH_SET_SONIC_TMPL, "'{0}'".format(TEST_CLR_QOS_JSON)])
        output = self.run_script(['get', PATH_GET_SONIC_TMPL, ''])
        output = "".join(output.replace('\n', '').split())
        self.chk_output(org_cfg, output, False)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestQos('test_set_sonic_qos_cfg'))
    suite.addTest(TestQos('test_clear_sonic_qos_cfg'))
    return suite

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', help="target url, typically localhost:<port>")
    parser.add_argument('--dbg', action="store_true", help="print debug messages")
    args = parser.parse_args()

    if args.target:
        TestQos.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestQos.dbg_print = args.dbg

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite())

