/*
 * Copyright 2016 The Android Open Source Project
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

#include <stdlib.h>

#include <string>

#include <utils/RefBase.h>
#define LOG_TAG "VtsFuzzerBinderService"
#include <utils/Log.h>

#include <binder/TextOutput.h>
#include <binder/IInterface.h>
#include <binder/IBinder.h>
#include <binder/ProcessState.h>
#include <binder/IServiceManager.h>
#include <binder/IPCThreadState.h>

#include "binder/VtsFuzzerBinderService.h"

using namespace std;


namespace android {
namespace vts {

IMPLEMENT_META_INTERFACE(VtsFuzzer, VTS_FUZZER_BINDER_SERVICE_NAME);


void BpVtsFuzzer::Exit() {
  Parcel data;
  Parcel reply;
  data.writeInterfaceToken(IVtsFuzzer::getInterfaceDescriptor());
  data.writeString16(String16("Exit code"));
  remote()->transact(EXIT, data, &reply, IBinder::FLAG_ONEWAY);
}


int32_t BpVtsFuzzer::LoadHal(const string& path, int target_class,
                             int target_type, float target_version) {
  Parcel data;
  Parcel reply;

  data.writeInterfaceToken(IVtsFuzzer::getInterfaceDescriptor());
  data.writeCString(path.c_str());
  data.writeInt32(target_class);
  data.writeInt32(target_type);
  data.writeFloat(target_version);

#ifdef VTS_FUZZER_BINDER_DEBUG
  aout << "BpVtsFuzzer::Status request parcel:\n";
  data.print(PLOG);
  endl(PLOG);
#endif

  remote()->transact(LOAD_HAL, data, &reply);

#ifdef VTS_FUZZER_BINDER_DEBUG
  aout << "BpVtsFuzzer::Status response parcel:\n";
  reply.print(PLOG);
  endl(PLOG);
#endif

  int32_t res;
  status_t status = reply.readInt32(&res);
  return res;
}


int32_t BpVtsFuzzer::Status(int32_t type) {
  Parcel data;
  Parcel reply;

  data.writeInterfaceToken(IVtsFuzzer::getInterfaceDescriptor());
  data.writeInt32(type);

#ifdef VTS_FUZZER_BINDER_DEBUG
  aout << "BpVtsFuzzer::Status request parcel:\n";
  data.print(PLOG);
  endl(PLOG);
#endif

  remote()->transact(STATUS, data, &reply);

#ifdef VTS_FUZZER_BINDER_DEBUG
  aout << "BpVtsFuzzer::Status response parcel:\n";
  reply.print(PLOG);
  endl(PLOG);
#endif

  int32_t res;
  status_t status = reply.readInt32(&res);
  return res;
}


int32_t BpVtsFuzzer::Call(int32_t arg1, int32_t arg2) {
  Parcel data, reply;
  data.writeInterfaceToken(IVtsFuzzer::getInterfaceDescriptor());
  data.writeInt32(arg1);
  data.writeInt32(arg2);
#ifdef VTS_FUZZER_BINDER_DEBUG
  data.print(PLOG);
  endl(PLOG);
#endif

  remote()->transact(CALL, data, &reply);
#ifdef VTS_FUZZER_BINDER_DEBUG
  reply.print(PLOG);
  endl(PLOG);
#endif

  int32_t res;
  status_t status = reply.readInt32(&res);
  return res;
}


const char* BpVtsFuzzer::GetFunctions() {
  Parcel data, reply;
  data.writeInterfaceToken(IVtsFuzzer::getInterfaceDescriptor());
#ifdef VTS_FUZZER_BINDER_DEBUG
  data.print(PLOG);
  endl(PLOG);
#endif

  remote()->transact(GET_FUNCTIONS, data, &reply);
#ifdef VTS_FUZZER_BINDER_DEBUG
  reply.print(PLOG);
  endl(PLOG);
#endif

  const char* res = reply.readCString();
  if (res == NULL) {
    printf("reply == NULL\n");
    return NULL;
  }

  printf("len(reply) = %d\n", strlen(res));
  char* result = (char*) malloc(strlen(res) + 1);
  strcpy(result, res);
  return (const char*) result;
}

}  // namespace vts
}  // namespace android
