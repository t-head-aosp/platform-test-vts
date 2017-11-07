/*
 * Copyright (C) 2017 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef UTILS_NATIVE_TESTABILITY_CHECKER_H_
#define UTILS_NATIVE_TESTABILITY_CHECKER_H_

#include <set>

#include <android-base/logging.h>
#include <vintf/CompatibilityMatrix.h>
#include <vintf/HalManifest.h>

using android::vintf::Arch;
using android::vintf::CompatibilityMatrix;
using android::vintf::HalManifest;
using android::vintf::ManifestHal;
using android::vintf::MatrixHal;
using android::vintf::Version;
using std::set;
using std::string;

namespace android {
namespace vts {

// Library class to decide whether to run a test against given hal based on
// the system compatibility matrix and device manifest files. Also collect the
// instance names for testing if the decision is true.
class VtsTestabilityChecker {
 public:
  VtsTestabilityChecker(const CompatibilityMatrix* framework_comp_matrix,
                        const HalManifest* framework_hal_manifest,
                        const HalManifest* device_hal_manifest)
      : framework_comp_matrix_(framework_comp_matrix),
        framework_hal_manifest_(framework_hal_manifest),
        device_hal_manifest_(device_hal_manifest) {
    CHECK(framework_comp_matrix_) << "framework_comp_matrix null.";
    CHECK(framework_hal_manifest_) << "framework_hal_manifest null.";
    CHECK(device_hal_manifest_) << "device_hal_manifest null.";
  };

  // Check whether we should run a compliance test against the given hal with
  // the package name, version and interface name. Arch (32 or 64) info is
  // required if the hal is a passthrough hal.
  // Return true to indicate we should run the test, false otherwise.
  // Store the instances name to run the test, instance should be empty set if
  // we determine not to run the test (i,e. return value false).
  bool CheckHalForComplianceTest(const string& hal_package_name,
                                 const Version& hal_version,
                                 const string& hal_interface_name,
                                 const Arch& arch, set<string>* instances);

  // Check whether we should run a non-compliance test against the given hal
  // with the package name, version and interface name. Arch (32 or 64) info is
  // required if the hal is a passthrough hal.
  // Return true to indicate we should run the test, false otherwise.
  // Store the instances name to run the test, instance should be empty set if
  // we determine not to run the test (i,e. return value false).
  bool CheckHalForNonComplianceTest(const string& hal_package_name,
                                    const Version& hal_version,
                                    const string& hal_interface_name,
                                    const Arch& arch, set<string>* instances);

 private:
  // Internal method to check the given hal against the framework compatibility
  // matrix and device manifest.
  // If the hal is required by the framework, return true with the corresponding
  // instance names. If the hal is optional for framework, return true if vendor
  // supports the hal with the corresponding instance names, false otherwise.
  bool CheckFrameworkCompatibleHal(const string& hal_package_name,
                                   const Version& hal_version,
                                   const string& hal_interface_name,
                                   const Arch& arch, set<string>* instances);

  // Internal method to check whether the given hal is supported by vendor
  // (i.e exists in the vendor manifest file). Store the corresponding instance
  // names if supported..
  // Arch (32 or 64) info is required if the hal is a passthrough hal.
  bool CheckVendorManifestHal(const string& hal_package_name,
                              const Version& hal_version,
                              const string& hal_interface_name,
                              const Arch& arch, set<string>* instances);

  // Internal method to check whether the given hal is supported by framework
  // (i.e exists in the framework manifest file). Store the corresponding
  // instance names if supported.
  // Arch (32 or 64) info is required if the hal is a passthrough hal.
  bool CheckFrameworkManifestHal(const string& hal_package_name,
                                 const Version& hal_version,
                                 const string& hal_interface_name,
                                 const Arch& arch, set<string>* instances);

  // Helper method to check whether the mantifest_hal support the interface
  // and arch (for passthrough hal). Store the corresponding
  // instance names if supported.
  bool CheckManifestHal(const ManifestHal* manifest_hal,
                        const string& hal_interface_name, const Arch& arch,
                        set<string>* instances);

  // Helper method to get the instance name for a given hal.
  // If both matrix_hal and manifest_hal not null (i.e. the given hal exists
  // in both compatibilty matrix and manifest), find the instance names in both
  // hal and return the intersection.
  // If either matrix_hal or manifest_hal not null, return the corresponding
  // instance names
  void GetTestInstances(const MatrixHal* matrix_hal,
                        const ManifestHal* manifest_hal,
                        const string& interface_name, set<string>* instances);

  // Helper method to check whether a passthrough hal support the given arch
  // (32 or 64).
  bool CheckPassthroughManifestHal(const ManifestHal* manifest_hal,
                                   const Arch& arch);

  const CompatibilityMatrix* framework_comp_matrix_;  // Do not own.
  const HalManifest* framework_hal_manifest_;         // Do not own.
  const HalManifest* device_hal_manifest_;            // Do not own.
};

}  // namespace vts
}  // namespace android
#endif  // UTILS_NATIVE_TESTABILITY_CHECKER_H_
