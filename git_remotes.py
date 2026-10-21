"""Video de Git, Parte II (en inglés): trabajar con remotos.
Cubre git clone, fetch, diff, merge, push y pull.

Ejecutar:
    uv run manim -pql git_remotes.py GitRemotes    # vista rápida
    uv run manim -pqh git_remotes.py GitRemotes    # calidad alta
"""

import textwrap

from manim import *

MONO = "Consolas"
PANEL_BG = "#1e1e1e"

# Geometría de cada grafo (relativa al origen de su repositorio)
DX = 1.3          # separación horizontal entre commits
LANE_DY = 0.8     # separación vertical entre carriles
NODE_R = 0.26

MAIN_COLOR = BLUE_C
HEAD_COLOR = YELLOW
ADD_COLOR = GREEN_C
DEL_COLOR = RED_C

READING_SPEED = 3.0  # palabras por segundo al calcular pausas de lectura

# Historia del proyecto: posición en el grafo, padres y contenido de story.txt
COMMITS = {
    "C1": dict(slot=0, lane=0, parents=[],
               files=["# My Story"]),
    "C2": dict(slot=1, lane=0, parents=["C1"],
               files=["# My Story", "Once upon a time..."]),
    "C3": dict(slot=2, lane=0, parents=["C2"],
               files=["# My Story", "Once upon a time...", "Ch1: The journey"]),
    # Commit de un compañero de equipo
    "C4": dict(slot=3, lane=0, parents=["C3"],
               files=["# My Story", "Once upon a time...", "Ch1: The journey",
                      "Ch2: The storm"]),
    # Commit propio, en paralelo a C4
    "C5": dict(slot=3, lane=1, parents=["C3"],
               files=["# My Story", "Once upon a time, far away...",
                      "Ch1: The journey"]),
    # Merge: combina ambos cambios
    "M": dict(slot=4, lane=0, parents=["C5", "C4"],
              files=["# My Story", "Once upon a time, far away...",
                     "Ch1: The journey", "Ch2: The storm"]),
    "C6": dict(slot=5, lane=0, parents=["M"],
               files=["# My Story", "Once upon a time, far away...",
                      "Ch1: The journey", "Ch2: The storm", "Ch3: The island"]),
}


def make_tag(name):
    """Etiqueta de referencia. origin/main va solo con borde para distinguirla."""
    if name == "origin/main":
        label = Text(name, font_size=16, weight=BOLD, color=MAIN_COLOR)
        box = RoundedRectangle(corner_radius=0.08, width=label.width + 0.26, height=0.34,
                               fill_color=PANEL_BG, fill_opacity=1,
                               stroke_color=MAIN_COLOR, stroke_width=2)
    else:
        color = HEAD_COLOR if name == "HEAD" else MAIN_COLOR
        label = Text(name, font_size=16, weight=BOLD, color=BLACK)
        box = RoundedRectangle(corner_radius=0.08, width=label.width + 0.26, height=0.34,
                               fill_color=color, fill_opacity=1, stroke_width=0)
    return VGroup(box, label)


class Repo:
    """Estado y mobjects de un repositorio (remoto o local)."""

    def __init__(self, origin):
        self.origin = np.array(origin)
        self.nodes = {}     # id -> mobject del commit
        self.refs = {}      # nombre de ref -> id de commit
        self.tags = {}      # nombre de ref -> mobject
        self.head = None    # branch a la que apunta HEAD (solo en el local)

    def pos(self, cid):
        c = COMMITS[cid]
        return self.origin + RIGHT * DX * c["slot"] + DOWN * LANE_DY * c["lane"]

    def make_node(self, cid):
        return VGroup(
            Circle(NODE_R, color=WHITE, stroke_width=3, fill_color=GREY_E, fill_opacity=1),
            Text(cid, font_size=16),
        ).move_to(self.pos(cid))

    def make_arrows(self, cid):
        return [Arrow(self.pos(cid), self.pos(p), buff=NODE_R + 0.03, stroke_width=3,
                      tip_length=0.13, color=GREY_B)
                for p in COMMITS[cid]["parents"]]

    def ref_targets(self):
        by_commit = {}
        for name, cid in self.refs.items():
            by_commit.setdefault(cid, []).append(name)
        targets = {}
        for cid, names in by_commit.items():
            # origin/main pegado al commit; la branch de HEAD hacia afuera
            names.sort(key=lambda n: (n != "origin/main", n == self.head))
            d = UP if COMMITS[cid]["lane"] == 0 else DOWN
            for k, n in enumerate(names):
                targets[n] = self.pos(cid) + d * (0.55 + 0.45 * k)
            if self.head in names:
                targets["HEAD"] = self.pos(cid) + d * (0.55 + 0.45 * len(names))
        return targets

    def ref_anims(self):
        anims = []
        for name, p in self.ref_targets().items():
            if name not in self.tags:
                self.tags[name] = make_tag(name).move_to(p)
                anims.append(FadeIn(self.tags[name], scale=0.5))
            else:
                anims.append(self.tags[name].animate.move_to(p))
        return anims


class GitRemotes(Scene):
    # ------------------------------------------------------------ utilidades
    def setup(self):
        self.caption = VMobject()
        self.cmd_text = VMobject()
        self.chapter_label = VMobject()
        self.panel_header = VMobject()
        self.panel_body = VMobject()
        self.wd = []

    def say(self, text, t2c=None, extra=0.0):
        """Muestra una explicación en la columna derecha y espera a que se lea."""
        new = Text(textwrap.fill(text, 34), font_size=24, line_spacing=1.1,
                   color=GREY_A, t2c=t2c or {})
        if new.width > 5.6:
            new.scale_to_fit_width(5.6)
        new.next_to(self.panel, DOWN, buff=0.4).align_to(self.panel, LEFT)
        self.play(FadeOut(self.caption), FadeIn(new), run_time=0.5)
        self.caption = new
        self.wait(len(text.split()) / READING_SPEED + extra)

    def run(self, cmd):
        """Escribe un comando en la barra de terminal."""
        new = Text(cmd, font=MONO, font_size=22).next_to(self.prompt, RIGHT, buff=0.2)
        self.play(FadeOut(self.cmd_text), run_time=0.2)
        self.play(AddTextLetterByLetter(new, run_time=max(0.5, 0.035 * len(cmd))))
        self.cmd_text = new

    def chapter(self, title):
        big = Text(title, font_size=56, weight=BOLD)
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                       fill_color=BLACK, fill_opacity=0.92, stroke_width=0)
        self.play(FadeIn(bg), FadeIn(big, scale=1.2), run_time=0.6)
        self.wait(0.8)
        small = Text(title, font_size=20, color=GREY_B).to_corner(UL, buff=0.2)
        self.play(FadeOut(bg), ReplacementTransform(big, small),
                  FadeOut(self.chapter_label), run_time=0.7)
        self.chapter_label = small

    # ------------------------------------------------------ panel derecho
    def set_panel(self, header, body):
        header.align_to(self.panel, UL).shift(RIGHT * 0.3 + DOWN * 0.25)
        body.next_to(header, DOWN, buff=0.35).align_to(header, LEFT)
        anims = [FadeOut(self.panel_header), FadeOut(self.panel_body),
                 FadeIn(header), FadeIn(body)]
        self.panel_header, self.panel_body = header, body
        return anims

    def show_file(self, lines, mark_new=False):
        """Animaciones para mostrar story.txt (el working directory local)."""
        body = VGroup(*[
            Text(l, font=MONO, font_size=20,
                 color=YELLOW_B if mark_new and l not in self.wd else WHITE)
            for l in lines
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        header = VGroup(
            Text("story.txt", font=MONO, font_size=18, color=GREY_B),
            Text("working directory", font_size=15, color=GREY_C, slant=ITALIC),
        ).arrange(RIGHT, buff=0.4)
        self.wd = list(lines)
        return self.set_panel(header, body)

    def show_diff(self, title, lines):
        """Animaciones para mostrar la salida de git diff: (signo, texto)."""
        colors = {"+": ADD_COLOR, "-": DEL_COLOR, " ": GREY_C}
        rows = VGroup()
        for sign, text in lines:
            # El signo va en su propia columna (Text descarta espacios iniciales)
            mark = Text(sign if sign != " " else "+", font=MONO, font_size=20,
                        color=colors[sign]).set_opacity(0 if sign == " " else 1)
            rows.add(VGroup(mark, Text(text, font=MONO, font_size=20, color=colors[sign])
                            ).arrange(RIGHT, buff=0.12))
        body = rows.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        header = Text(title, font=MONO, font_size=18, color=GREY_B)
        return self.set_panel(header, body)

    # ---------------------------------------------------------- acciones
    def new_commit(self, repo, cid):
        """Crea un commit nuevo en un repo (sin copiarlo de otro)."""
        repo.nodes[cid] = repo.make_node(cid)
        arrows = repo.make_arrows(cid)
        self.play(*[GrowArrow(a) for a in arrows], GrowFromCenter(repo.nodes[cid]))

    def transfer(self, src, dst, cids, run_time=1.2):
        """Copia commits de un repo a otro (clone, fetch, push)."""
        for cid in cids:
            dst.nodes[cid] = dst.make_node(cid)
        self.play(LaggedStart(*[TransformFromCopy(src.nodes[c], dst.nodes[c])
                                for c in cids], lag_ratio=0.25), run_time=run_time)
        arrows = [a for c in cids for a in dst.make_arrows(c)]
        self.play(*[GrowArrow(a) for a in arrows], run_time=0.6)

    def make_box(self, center, width, height, title, color):
        box = RoundedRectangle(corner_radius=0.2, width=width, height=height,
                               stroke_color=color, stroke_width=2).move_to(center)
        label = Text(title, font_size=18, color=color, weight=BOLD)
        label.add_background_rectangle(color=BLACK, opacity=1, buff=0.1)
        label.move_to(box.get_top()).align_to(box, LEFT).shift(RIGHT * 0.35)
        return VGroup(box, label)

    # =============================================================== guion
    def construct(self):
        self.intro()
        self.build_layout()
        self.part_clone()
        self.part_fetch()
        self.part_diff()
        self.part_merge()
        self.part_push()
        self.part_pull()
        self.recap()

    def intro(self):
        title = Text("Git, Visually — Part II", font_size=60, weight=BOLD)
        sub = Text("Working with remotes: clone, fetch, diff, merge, push, pull",
                   font_size=28, color=GREY_A)
        VGroup(title, sub).arrange(DOWN, buff=0.4)
        self.play(Write(title), run_time=1.2)
        self.play(FadeIn(sub, shift=UP * 0.2))
        self.wait(2)
        self.play(FadeOut(title, sub))

    def build_layout(self):
        bar = RoundedRectangle(width=13.6, height=0.5, corner_radius=0.1,
                               fill_color=PANEL_BG, fill_opacity=1,
                               stroke_color=GREY_D).move_to([0, 3.1, 0])
        self.prompt = Text("$", font=MONO, font_size=22, color=GREEN_C)
        self.prompt.move_to(bar).align_to(bar, LEFT).shift(RIGHT * 0.25)

        self.panel = RoundedRectangle(width=5.6, height=2.9, corner_radius=0.15,
                                      fill_color=PANEL_BG, fill_opacity=1,
                                      stroke_color=GREY_D).move_to([4.1, 1.2, 0])

        self.remote_box = self.make_box([-2.95, 1.43, 0], 7.9, 2.45,
                                        "GitHub  ·  origin", PURPLE_B)
        self.local_box = self.make_box([-2.95, -2.0, 0], 7.9, 3.9,
                                       "Your computer", TEAL_C)
        self.remote = Repo([-6.45, 1.35, 0])
        self.local = Repo([-6.45, -1.75, 0])

        self.play(FadeIn(bar, self.prompt, self.panel))

    # ------------------------------------------------------- 1. clone
    def part_clone(self):
        self.chapter("1. Remotes & git clone")
        r = self.remote
        self.play(Create(self.remote_box[0]), FadeIn(self.remote_box[1]))
        for cid in ["C1", "C2", "C3"]:
            r.nodes[cid] = r.make_node(cid)
        arrows = [a for c in ["C2", "C3"] for a in r.make_arrows(c)]
        r.refs["main"] = "C3"
        self.play(LaggedStart(*[GrowFromCenter(r.nodes[c]) for c in ["C1", "C2", "C3"]],
                              lag_ratio=0.3),
                  *[GrowArrow(a) for a in arrows], *r.ref_anims())
        self.say("Your project usually also lives on a server like GitHub. "
                 "Git calls it a remote, and names it origin.",
                 t2c={"remote,": PURPLE_B, "origin.": PURPLE_B})

        self.run("git clone https://github.com/you/story.git")
        self.play(Create(self.local_box[0]), FadeIn(self.local_box[1]))
        l = self.local
        self.transfer(r, l, ["C1", "C2", "C3"])
        l.refs.update({"main": "C3", "origin/main": "C3"})
        l.head = "main"
        self.play(*l.ref_anims(), *self.show_file(COMMITS["C3"]["files"]))
        self.say("git clone downloads the whole history, not just the latest "
                 "files, and checks out main.", t2c={"main.": MAIN_COLOR})
        self.play(Indicate(l.tags["origin/main"], color=MAIN_COLOR))
        self.say("origin/main is a bookmark: where main was on GitHub the last "
                 "time you talked to it.", t2c={"origin/main": MAIN_COLOR})

    # ------------------------------------------------------- 2. fetch
    def part_fetch(self):
        self.chapter("2. git fetch")
        r, l = self.remote, self.local
        self.new_commit(r, "C4")
        r.refs["main"] = "C4"
        note = Text("pushed by a teammate", font_size=16, color=GREY_B, slant=ITALIC)
        note.next_to(r.nodes["C4"], DOWN, buff=0.15)
        self.play(*r.ref_anims(), FadeIn(note))
        self.say("Meanwhile, a teammate pushes a new commit to GitHub. "
                 "Your computer doesn't know about it yet.")
        self.play(FadeOut(note))

        self.run("git fetch")
        self.transfer(r, l, ["C4"])
        l.refs["origin/main"] = "C4"
        self.play(*l.ref_anims())
        self.say("git fetch downloads new commits and moves origin/main. "
                 "Your main branch and your files stay untouched.",
                 t2c={"origin/main.": MAIN_COLOR})
        self.say("That makes fetch always safe: it looks, but never changes your work.")

    # -------------------------------------------------------- 3. diff
    def part_diff(self):
        self.chapter("3. git diff")
        l = self.local
        self.run("git diff main origin/main")
        self.play(*self.show_diff("$ git diff main origin/main", [
            (" ", "# My Story"), (" ", "Once upon a time..."),
            (" ", "Ch1: The journey"), ("+", "Ch2: The storm"),
        ]))
        self.say("git diff compares two commits. Lines starting with + were added; "
                 "lines with - were removed.",
                 t2c={"+": ADD_COLOR, "-": DEL_COLOR})
        self.say("Here we preview what our teammate changed before bringing it in.")

        self.play(*self.show_file(COMMITS["C3"]["files"]))
        self.play(*self.show_file(COMMITS["C5"]["files"], mark_new=True))
        self.say("Now let's edit the intro ourselves. Yellow means not committed yet.",
                 t2c={"Yellow": YELLOW_B})

        self.run("git diff")
        self.play(*self.show_diff("$ git diff", [
            (" ", "# My Story"), ("-", "Once upon a time..."),
            ("+", "Once upon a time, far away..."), (" ", "Ch1: The journey"),
        ]))
        self.say("With no arguments, git diff shows your uncommitted changes: "
                 "exactly what your next commit would save.")

        self.run('git commit -am "Expand intro"')
        self.new_commit(l, "C5")
        l.refs["main"] = "C5"
        self.play(*l.ref_anims(), *self.show_file(COMMITS["C5"]["files"]))
        self.say("After committing, main and origin/main have diverged: "
                 "each has a commit the other doesn't.",
                 t2c={"diverged:": YELLOW})

    # ------------------------------------------------------- 4. merge
    def part_merge(self):
        self.chapter("4. git merge")
        l = self.local
        self.say("To combine both lines of work, we merge.")
        self.run("git merge origin/main")
        self.new_commit(l, "M")
        l.refs["main"] = "M"
        self.play(*l.ref_anims(), *self.show_file(COMMITS["M"]["files"]))
        self.play(*[Indicate(l.nodes[c], color=YELLOW) for c in ["C4", "C5"]])
        self.say("Git creates a merge commit with two parents. "
                 "Our file now contains both changes.")
        self.say("If both sides edited the same lines, Git can't decide alone: "
                 "it stops and asks you to resolve a conflict.",
                 t2c={"conflict.": DEL_COLOR})

    # -------------------------------------------------------- 5. push
    def part_push(self):
        self.chapter("5. git push")
        r, l = self.remote, self.local
        self.say("GitHub still doesn't have C5 or the merge commit. Let's upload them.")
        self.run("git push")
        self.transfer(l, r, ["C5", "M"])
        r.refs["main"] = "M"
        l.refs["origin/main"] = "M"
        self.play(*r.ref_anims(), *l.ref_anims())
        self.say("git push uploads your commits and moves main on GitHub. "
                 "Your origin/main bookmark updates too.",
                 t2c={"origin/main": MAIN_COLOR})
        self.say("Push is rejected if GitHub has commits you don't have. "
                 "That's why we merged first.", t2c={"rejected": DEL_COLOR})

    # -------------------------------------------------------- 6. pull
    def part_pull(self):
        self.chapter("6. git pull")
        r, l = self.remote, self.local
        self.new_commit(r, "C6")
        r.refs["main"] = "C6"
        self.play(*r.ref_anims())
        self.say("Our teammate pushes again. This time we'll use the shortcut.")

        self.run("git pull")
        step = Text("1) fetch", font=MONO, font_size=20, color=YELLOW)
        step.next_to(self.cmd_text, RIGHT, buff=0.6)
        self.play(FadeIn(step))
        self.transfer(r, l, ["C6"])
        l.refs["origin/main"] = "C6"
        self.play(*l.ref_anims())

        step2 = Text("2) merge", font=MONO, font_size=20, color=YELLOW)
        step2.next_to(step, RIGHT, buff=0.4)
        self.play(FadeIn(step2))
        l.refs["main"] = "C6"
        self.play(*l.ref_anims(), *self.show_file(COMMITS["C6"]["files"]))
        self.say("git pull is git fetch plus git merge in a single command.",
                 t2c={"git fetch": YELLOW, "git merge": YELLOW})
        self.say("Since we had no new local commits, main just moves forward. "
                 "This is called a fast-forward: no merge commit needed.",
                 t2c={"fast-forward:": YELLOW})
        self.play(FadeOut(step, step2))

    # ---------------------------------------------------------- resumen
    def recap(self):
        cortina = Rectangle(width=config.frame_width, height=config.frame_height,
                            fill_color=BLACK, fill_opacity=1, stroke_width=0)
        self.play(FadeIn(cortina))
        self.clear()
        title = Text("Recap", font_size=48, weight=BOLD).to_edge(UP, buff=0.5)
        rows = [
            ("git clone <url>", "copy a remote repository to your computer"),
            ("git fetch", "download new commits, update origin/main"),
            ("git diff", "see changes: uncommitted, or between commits"),
            ("git merge <branch>", "combine another branch into yours"),
            ("git push", "upload your commits to the remote"),
            ("git pull", "fetch + merge in one step"),
        ]
        table = VGroup()
        for left, right in rows:
            l = Text(left, font=MONO, font_size=24, color=YELLOW)
            r = Text(right, font_size=24, color=GREY_A)
            l.move_to([-6.2, 0, 0], aligned_edge=LEFT)
            r.move_to([-1.6, 0, 0], aligned_edge=LEFT)
            table.add(VGroup(l, r))
        table.arrange(DOWN, buff=0.38, aligned_edge=LEFT).next_to(title, DOWN, buff=0.6)
        table.set_x(0)
        rule = Text("Golden rule: pull before you push.",
                    font_size=28, color=YELLOW).to_edge(DOWN, buff=0.6)

        self.play(Write(title))
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in table],
                              lag_ratio=0.3), run_time=3)
        self.wait(6)
        self.play(Write(rule))
        self.wait(4)
