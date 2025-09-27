"""Chat type interaction for accountant."""

import membank

from . import brain, memories, chat_interface, handlers, process


def conversation(talker, text, files, callback, conf):
    """Make conversation.

    Receive text and send message back via callback.
    """
    talk = Chat(talker, conf, callback)
    if talk.ongoing:
        if talk.subject:
            talk.do_subject(text, files)
            talk.action()
        else:
            if not talk.get_subject(text):
                callback(
                    "I didn't get. Would you like me to send full list of commands?"
                )
                talk.set_subject("do_get_help")
            else:
                talk.action()
    else:
        talk.ongoing = True
        if not talk.get_subject(text):
            callback("What would you like me to do?")
        else:
            talk.action()


# pylint: disable=too-many-instance-attributes
class Chat:
    """Interface for communication and routing with talker."""

    def __init__(self, talker, conf, callback):
        """Initialise comm interface with talker."""
        self._m = membank.LoadMemory(conf.get("db_path"))
        self._t = self._m.get.conversation(talker=talker)
        if not self._t:
            self._t = memories.Conversation(
                talker=talker,
            )
        self._call = callback
        self._conf = conf
        self._interface = chat_interface.Interface()
        self._interface_ready = self._load_interface()

    @property
    def talker(self):
        """Return talker."""
        return self._t.talker

    @property
    def ongoing(self):
        """Check if talk is ongoing."""
        return self._t.ongoing

    @ongoing.setter
    def ongoing(self, value):
        """Set talk ongoing value."""
        self._t.ongoing = value
        self._m.put(self._t)

    @property
    def subject(self):
        """Return subject if present."""
        return self._t.subject

    def action(self):
        """Check if ready for action, if so executes otherwise asks info."""
        if self.is_complete():
            self.perform()
        else:
            self.ask_missing()

    def get_subject(self, text):
        """Try to understand subject from text.

        if understood set the subject and return it otherwise return
        None.
        """
        subj = self._m.get.chatsubjectlookup(sentence=text)
        if subj:
            self.set_subject(subj.cmd)
        else:
            cmd_list = [
                " ".join(i.split("_")) for i in brain.generate_cmd_list()
            ]
            pos = process.extractOne(text, cmd_list)
            if pos[1] >= 95:
                cmd = pos[0].replace(" ", "_")
                self._m.put(memories.ChatSubjectLookup(cmd, text))
                subj = cmd
                self.set_subject(subj)
        return subj

    def set_subject(self, cmd):
        """Set subject as per cmd."""
        self._t.subject = cmd
        self._m.put(self._t)
        self._interface_ready = self._load_interface()

    def clear_subject(self):
        """Reset conversation to new start."""
        self.set_subject("")
        self._call("OK. Let's start over.")

    def do_subject(self, text, attach):
        """Continue on the subject."""
        if self._positive(text):
            self._load_data(text, attach[0])

    def _positive(self, text):
        """Assert that text seems positive otherwise cancels the subject."""
        choices = [
            "no",
            "cancel",
            "stop",
            "stop it",
            "forget",
            "start again",
            "naah",
        ]
        pos = process.extractOne(text, choices)
        if pos[1] > 97:
            self.clear_subject()
            return False
        return True

    def _load_data(self, text, attachment):
        """Load text and attachment as per subject interface."""
        auxes = False
        if self._interface.auxiliaries:
            for support in self._interface.auxiliaries:
                answer = support(text, self._t)
                if answer:
                    self._call(answer)
                    self._m.put(self._t)
                    auxes = True
                    break
        if auxes:
            return  # noqa: E701
        try:
            data = handlers.get_json(text)
        except RuntimeWarning as err:
            self._call(err)
        if attachment and self._interface.attachment:
            self._t.attachment = attachment
            self._m.put(self._t)
        elif attachment:
            self._call("I don't need attachment so I ignore it")
        fields = self._interface.required.union(self._interface.optional)
        if len(data) > 1:
            self._call("Sorry not more than record. Do not duplicate fields")
        elif len(data) == 1:
            data = data[0]
            for key in data:
                if key in fields:
                    self._t.data[key] = data[key]
                    self._m.put(self._t)
                else:
                    self._call(f"Field '{key}' is not valid, ignoring")

    def _load_interface(self):
        """Load interface demands marks internal flag if succesfull."""
        if not self._t.subject:
            return False
        if self._t.subject not in dir(chat_interface):
            msg = f"Ups. I am confused, don't know what to do with '{self._t.subject}'"
            self._call(msg)
            return False
        interface = getattr(chat_interface, self._t.subject)
        self._interface = interface()
        return True

    def is_complete(self):
        """Check if subject interface is complete and ready to pass on."""
        if not self._interface_ready:
            return False
        keys = self._t.data.keys()
        for req in self._interface.required:
            if req not in keys:
                return False
        if self._interface.one_optional and not keys:
            return False
        return self._interface.attachment == bool(self._t.attachment)

    def perform(self):
        """Perform a task."""
        msg, attach, fname = brain.do_task(
            self._conf,
            self._m,
            self._t.subject,
            [self._t.data],
            self._t.attachment,
        )
        self._call(msg, attach, fname)
        self._t.subject = ""
        self._t.attachment = b""
        self._t.data = {}
        self._m.put(self._t)

    def ask_missing(self):
        """Send missing data requirements."""
        msg = ""
        keys = self._t.data.keys()
        mand = []
        for req in self._interface.required:
            if req not in keys:
                mand.append(req)
        attach = self._interface.attachment == bool(self._t.attachment)
        opts = []
        for opt in self._interface.optional:
            if opt not in keys:
                opts.append(opt)
        if mand:
            msg += "I miss fields: " + ", ".join(mand)
        if opts:
            if msg:
                msg += "\n"
            msg += "Optional fields: " + ", ".join(opts)
        if not attach:
            if msg:
                msg += "\n"
            msg += "I need attachment"
        if msg:
            self._call(msg)
