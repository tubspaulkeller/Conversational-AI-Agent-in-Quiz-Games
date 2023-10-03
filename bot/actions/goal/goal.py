class Goal:
    def __init__(self, is_group, id):
        self.id = id
        self.exceeded = False
        self.evaluated = False

        if is_group:
            self.text = "Ihr habt jetzt kurz Zeit, um euch auf das kommende Quizspiel vorzubereiten. Gemeinsam sollt ihr ein klares, präzises Ziel für euer Team festlegen, das die SMART-Kriterien erfüllt (spezifisch, messbar, erreichbar, relevant und zeitgebunden). Nachdem der Countdown abgelaufen ist, werde ich das Ziel von euch erfragen und daraufhin Feedback geben. 🤓"         
            self.task = "👋 %s schreib mir nun euer Ziel und markiert es mit einem #-Zeichen (#Ziel). 😎 "
        else:
            self.text = "Du hast nun kurz Zeit, dich auf das kommende Quizspiel vorzubereiten. Du sollst ein klares, präzises Ziel für dich festlegen, das die SMART-Kriterien erfüllt (spezifisch, messbar, erreichbar, relevant und zeitgebunden). Nachdem der Countdown abgelaufen ist, werde ich das Ziel von dir erfragen und daraufhin Feedback geben. 🤓"         
            self.task = "👋 %s schreib mir nun dein Ziel und markiere es mit einem #-Zeichen (#Ziel). 😎 "

    def to_dict(self):
        return {
            'id': self.id,
            'exceeded': self.exceeded,
            'evaluated': self.evaluated,
            'text': self.text,
            'task': self.task
        }