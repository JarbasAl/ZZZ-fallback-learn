# Copyright 2017 Mycroft AI, Inc.
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

from os.path import join
from mycroft.skills.core import FallbackSkill
from mycroft.util.parse import normalize
import random


class LearnUnknownSkill(FallbackSkill):
    def __init__(self):
        super(LearnUnknownSkill, self).__init__()
        # start a utterance database
        if "db" not in self.settings:
            self.settings["db"] = {self.lang: {}}

    def initialize(self):
        # high priority to always call handler
        self.register_fallback(self.handle_fallback, 1)

        # register learned utterances
        self.create_learned_intents()

        # TODO intent to ask answer samples and update db
        # TODO the answer for X is Y intent

    def handle_learn(self, message):
        utterances = self.settings["db"][self.lang]
        # if there are utterances in db
        if len(utterances):
            # pick a random one
            utterance = random.choice(utterances.keys())
            answers = utterances[utterance]
            # if less than 2 sample answers
            if len(answers) < 2:
                # ask user for answer
                question = self.dialog_renderer.render("what.answer", {"question": utterance})
                answer = self.get_response(question)
                if answer:
                    # if user answered add to database
                    self.add_utterances_to_db(utterance, answer, self.lang)

    def add_utterances_to_db(self, utterances, answers=None, lang=None):
        # accept string or list input
        if not isinstance(answers, list):
            answers = [answers]

        if not isinstance(utterances, list):
            utterances = [utterances]

        lang = lang or self.lang

        # store utterances in db for later learning
        if lang not in self.settings["db"]:
            self.settings["db"][lang] = {}

        for utterance in utterances:
            if utterance not in self.settings["db"][lang]:
                self.settings["db"][lang][utterance] = answers
            else:
                self.settings["db"][lang][utterance] += answers

        # optionally do a manual settings save
        self.settings.store()

    def create_learned_intents(self):
        utterances = self.settings["db"][self.lang]
        for utterance in utterances:
            answers = utterances[utterance]
            if len(answers):
                # create intent file for padatious
                path = join(self._dir, "vocab", self.lang,
                            utterance+".intent")
                with open(path, "w") as f:
                    f.write(utterance)

                # create learned answers dialog file
                path = join(self._dir, "dialog", self.lang,
                            utterance + ".dialog")
                with open(path, "w") as f:
                    f.writelines(answers)

                # create simple handler that speak dialog
                def handler(message):
                    self.speak_dialog(utterance)

                # register learned intent
                self.register_intent_file(utterance + '.intent', handler)

    def handle_fallback(self, message):
        lang = message.data.get("lang", self.lang)
        utterance = normalize(message.data['utterance'], lang=lang)

        # add utterance to db without answers
        self.add_utterances_to_db(utterance, lang=lang)

        # always return False so other fallbacks may still trigger
        return False


def create_skill():
    return LearnUnknownSkill()
