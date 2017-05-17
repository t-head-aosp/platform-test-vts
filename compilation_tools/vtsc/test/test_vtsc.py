#!/usr/bin/env python
#
# Copyright 2016 - The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import difflib
import filecmp
import getopt
import logging
import os
import shutil
import subprocess
import sys
import unittest

from vts.utils.python.common import cmd_utils


class VtscTester(unittest.TestCase):
    """Integration test runner for vtsc in generating the driver/profiler code.

    Runs vtsc with specified mode on a bunch of files and compares the output
    results with canonical ones. Exit code is 0 iff all tests pass.
    Note: need to run the script from the source root to preserve the correct
          path.

    Usage:
        python test_vtsc.py path_to_vtsc canonical_dir output_dir

    example:
        python test/vts/compilation_tools/vtsc/test/test_vtsc.py vtsc
        test/vts/compilation_tools/vtsc/test/golden/ temp_output

    Attributes:
        _hidl_gen_path: the path to run hidl-gen
        _vtsc_path: the path to run vtsc.
        _canonical_dir: root directory contains canonical files for comparison.
        _output_dir: root directory that stores all output files.
        _errors: number of errors generates during the test.
        _temp_dir: temp dir to store the .vts file generated by hidl-gen.
    """

    def __init__(self, testName, hidl_gen_path, vtsc_path, canonical_dir,
                 output_dir, temp_dir):
        super(VtscTester, self).__init__(testName)
        self._hidl_gen_path = hidl_gen_path
        self._vtsc_path = vtsc_path
        self._canonical_dir = canonical_dir
        self._output_dir = output_dir
        self._errors = 0
        self._temp_dir = temp_dir

    def setUp(self):
        """Removes output dir to prevent interference from previous runs."""
        self.RemoveOutputDir()

    def tearDown(self):
        """If successful, removes the output dir for clean-up."""
        if self._errors == 0:
            self.RemoveOutputDir()

    def testAll(self):
        """Run all tests. """
        self.TestDriver()
        self.TestProfiler()
        self.TestFuzzer()
        self.assertEqual(self._errors, 0)

    def TestDriver(self):
        """Run tests for DRIVER mode. """
        logging.info("Running TestDriver test case.")
        # Tests for Hidl Hals.
        for package_path, component_names in zip(
            ["android.hardware.nfc@1.0",
             "android.hardware.tests.bar@1.0"],
            [["Nfc", "NfcClientCallback", "types"],
             ["Bar"]]):
            self.GenerateVtsFile(package_path)
            for component_name in component_names:
                self.RunTest(
                    "DRIVER",
                    os.path.join(self._temp_dir, component_name + ".vts"),
                    "%s.vts.h" % component_name,
                    header_file_name="%s.vts.h" % component_name,
                    file_type="HEADER")
                self.RunTest(
                    "DRIVER",
                    os.path.join(self._temp_dir, component_name + ".vts"),
                    "%s.driver.cpp" % component_name,
                    file_type="SOURCE")
        # Tests for conventional Hals.
        for package_path, component_name in zip(
            ["camera/2.1", "bluetooth/1.0", "bluetooth/1.0", "wifi/1.0"], [
                "CameraHalV2", "BluetoothHalV1",
                "BluetoothHalV1bt_interface_t", "WifiHalV1"
            ]):
            self.RunTest("DRIVER",
                         "test/vts/specification/hal/conventional/%s/%s.vts" %
                         (package_path,
                          component_name), "%s.driver.cpp" % component_name)
        # Tests for shared libraries.
        for component_name in ["libcV1"]:
            self.RunTest("DRIVER",
                         "test/vts/specification/lib/ndk/bionic/1.0/%s.vts" %
                         component_name, "%s.driver.cpp" % component_name)

    def TestProfiler(self):
        """Run tests for PROFILER mode. """
        logging.info("Running TestProfiler test case.")
        self.GenerateVtsFile("android.hardware.nfc@1.0")
        for component_name in ["Nfc", "types", "NfcClientCallback"]:
            self.RunTest(
                "PROFILER",
                os.path.join(self._temp_dir, component_name + ".vts"),
                "%s.vts.h" % component_name,
                header_file_name="%s.vts.h" % component_name,
                file_type="HEADER")
            self.RunTest(
                "PROFILER",
                os.path.join(self._temp_dir, component_name + ".vts"),
                "%s.profiler.cpp" % component_name,
                file_type="SOURCE")

    def TestFuzzer(self):
        """Run tests for Fuzzer mode. """
        logging.info("Running TestProfiler test case.")
        self.GenerateVtsFile("android.hardware.renderscript@1.0")
        for component_name in ["Context", "Device", "types"]:
            self.RunTest(
                "FUZZER",
                os.path.join(self._temp_dir, component_name + ".vts"),
                "%s.fuzzer.cpp" % component_name,
                file_type="SOURCE")

    def RunFuzzerTest(self, mode, vts_file_path, source_file_name):
        vtsc_cmd = [
            self._vtsc_path, "-m" + mode, vts_file_path,
            os.path.join(self._output_dir, mode),
            os.path.join(self._output_dir, mode, "")
        ]
        return_code = cmd_utils.RunCommand(vtsc_cmd)

        canonical_source_file = os.path.join(self._canonical_dir, mode,
                                             source_file_name)
        output_source_file = os.path.join(self._output_dir, mode,
                                          source_file_name)
        self.CompareOutputFile(output_source_file, canonical_source_file)

    def GenerateVtsFile(self, hal_package_name):
        """Run hidl-gen to generate the .vts files for the give hal package.

        Args:
            hal_package_name: name of hal package e.g. android.hardware.nfc@1.0
        """
        hidl_gen_cmd = [
            self._hidl_gen_path, "-o" + self._temp_dir, "-Lvts",
            "-randroid.hardware:hardware/interfaces",
            "-randroid.hidl:system/libhidl/transport", hal_package_name
        ]
        return_code = cmd_utils.RunCommand(hidl_gen_cmd)
        if (return_code != 0):
            self.Error("Fail to execute command: %s" % hidl_gen_cmd)
        [hal_name, hal_version] = hal_package_name.split("@")
        output_dir = os.path.join(self._temp_dir,
                                  hal_name.replace(".", "/"), hal_version)
        for file in os.listdir(output_dir):
            if file.endswith(".vts"):
                os.rename(
                    os.path.join(output_dir, file),
                    os.path.join(self._temp_dir, file))

    def RunTest(self,
                mode,
                vts_file_path,
                output_file_name,
                header_file_name="",
                file_type="BOTH"):
        """Run vtsc with given mode for the give vts file and compare the
           output results.

        Args:
            mode: the vtsc mode for generated code. e.g. DRIVER / PROFILER.
            vts_file_path: path of the input vts file.
            source_file_name: name of the generated source file.
            file_type: type of file e.g. HEADER / SOURCE / BOTH.
        """
        if (file_type == "BOTH"):
            vtsc_cmd = [
                self._vtsc_path, "-m" + mode, vts_file_path,
                os.path.join(self._output_dir, mode),
                os.path.join(self._output_dir, mode, output_file_name)
            ]
        else:
            vtsc_cmd = [
                self._vtsc_path, "-m" + mode, "-t" + file_type, vts_file_path,
                os.path.join(self._output_dir, mode, output_file_name)
            ]
        return_code = cmd_utils.RunCommand(vtsc_cmd)
        if (return_code != 0):
            self.Error("Fail to execute command: %s" % vtsc_cmd)

        if (file_type == "HEADER" or file_type == "BOTH"):
            if not header_file_name:
                header_file_name = vts_file_path + ".h"
            canonical_header_file = os.path.join(self._canonical_dir, mode,
                                                 header_file_name)
            output_header_file = os.path.join(self._output_dir, mode,
                                              header_file_name)
            self.CompareOutputFile(output_header_file, canonical_header_file)
        elif (file_type == "SOURCE" or file_type == "BOTH"):
            canonical_source_file = os.path.join(self._canonical_dir, mode,
                                                 output_file_name)
            output_source_file = os.path.join(self._output_dir, mode,
                                              output_file_name)
            self.CompareOutputFile(output_source_file, canonical_source_file)
        else:
            self.Error("No such file_type: %s" % file_type)

    def CompareOutputFile(self, output_file, canonical_file):
        """Compares a given file and the corresponding one under canonical_dir.

        Args:
            canonical_file: name of the canonical file.
            output_file: name of the output file.
        """
        if not os.path.isfile(canonical_file):
            self.Error("Generated unexpected file: %s (for %s)" %
                       (output_file, canonical_file))
        else:
            if not filecmp.cmp(output_file, canonical_file):
                self.Error(
                    "output file: %s does not match the canonical_file: "
                    "%s" % (output_file, canonical_file))
                self.PrintDiffFiles(output_file, canonical_file)

    def PrintDiffFiles(self, output_file, canonical_file):
        with open(output_file, 'r') as file1:
            with open(canonical_file, 'r') as file2:
                diff = difflib.unified_diff(
                    file1.readlines(),
                    file2.readlines(),
                    fromfile=output_file,
                    tofile=canonical_file)
        for line in diff:
            logging.error(line)

    def Error(self, string):
        """Prints an error message and increments error count."""
        logging.error(string)
        self._errors += 1

    def RemoveOutputDir(self):
        """Remove the output_dir if it exists."""
        if os.path.exists(self._output_dir):
            logging.info("rm -rf %s", self._output_dir)
            shutil.rmtree(self._output_dir)
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)


if __name__ == "__main__":
    # Default values of the input parameter, could be overridden by command.
    vtsc_path = "vtsc"
    canonical_dir = "test/vts/compilation_tools/vtsc/test/golden/"
    output_dir = "test/vts/compilation_tools/vtsc/test/temp_coutput/"
    # Parse the arguments and set the provided value for
    # hidl-gen/vtsc_path/canonical_dar/output_dir.
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "h:p:c:o:t:")
    except getopt.GetoptError, err:
        print "Usage: python test_vtsc.py [-h hidl_gen_path] [-p vtsc_path] " \
              "[-c canonical_dir] [-o output_dir] [-t temp_dir]"
        sys.exit(1)
    for opt, val in opts:
        if opt == "-h":
            hidl_gen_path = val
        elif opt == "-p":
            vtsc_path = val
        elif opt == "-c":
            canonical_dir = val
        elif opt == "-o":
            output_dir = val
        elif opt == "-t":
            temp_dir = val
        else:
            print "unhandled option %s" % (opt, )
            sys.exit(1)

    suite = unittest.TestSuite()
    suite.addTest(
        VtscTester('testAll', hidl_gen_path, vtsc_path, canonical_dir,
                   output_dir, temp_dir))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        sys.exit(-1)
