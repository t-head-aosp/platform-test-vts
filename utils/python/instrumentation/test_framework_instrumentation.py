#
# Copyright (C) 2018 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging
import time

from vts.utils.python.instrumentation import test_framework_instrumentation_categories as tfic
from vts.utils.python.instrumentation import test_framework_instrumentation_event as tfie


# global category listing
categories = tfic.TestFrameworkInstrumentationCategories()
counts = {}

DEFAULT_CATEGORY = 'Misc'


def Begin(name, category=DEFAULT_CATEGORY, enable_logging=None, disable_subevent_logging=False):
    """Marks the beginning of an event.

    Params:
        name: string, name of the event.
        category: string, category of the event. Default category will be used if not specified.
        enable_logging: bool or None. Whether to put the event in logging.
                        Should be set to False when timing small pieces of code that could take
                        very short time to run.
                        If not specified or is None, global configuration will be used.
        disable_subevent_logging: bool, whether to disable logging for events created after this
                                  event begins and before this event ends. This will overwrite
                                  subevent's logging setting if set to True.

    Returns:
        Event object representing the event
    """
    event = tfie.TestFrameworkInstrumentationEvent(name, category)
    event.Begin(enable_logging=enable_logging, disable_subevent_logging=disable_subevent_logging)
    return event


def End(name, category=DEFAULT_CATEGORY):
    """Marks the end of an event.

    This function tries to find an event in internal event stack by calling FindEvent
    method with the given category and name.

    Will log error and return None if no match is found.

    If multiple event with the same category and name are found, the last one will be used.

    Use this function with caution if there are multiple events began with the same name and
    category. It is highly recommended to call End() method from the Event object directly.

    Params:
        name: string, name of the event.
        category: string, category of the event. Default category will be used if not specified.

    Returns:
        Event object representing the event. None if cannot find an active matching event
    """
    event = FindEvent(name, category)
    if not event:
        logging.error('Event with category %s and name %s either does not '
                      'exists or has already ended. Skipping...', name, category)
        return None

    event.End()
    return event


def FindEvent(name, category=DEFAULT_CATEGORY):
    """Finds an existing event that has started given the names.

    Use this function with caution if there are multiple events began with the same name and
    category. It is highly recommended to call End() method from the Event object directly.

    Params:
        name: string, name of the event.
        category: string, category of the event. Default category will be used if not specified.

    Returns:
        TestFrameworkInstrumentationEvent object if found; None otherwise.
    """
    for event in reversed(tfie.event_stack):
        if event.Match(name, category):
            return event

    return None


def Count(name, category=DEFAULT_CATEGORY):
    """Counts the occurrence of an event.

    Events will be mapped using name and category as key.

    Params:
        name: string, name of the event.
        category: string, category of the event. Default category will be used if not specified.
    """
    name, category = tfie.NormalizeNameCategory(name, category)
    # TODO(yuexima): give warning when there's illegal char, but only once for each combination.'
    if (name, category) not in counts:
        counts[(name, category)] = [time.clock()]
    else:
        counts[name, category].append(time.clock())