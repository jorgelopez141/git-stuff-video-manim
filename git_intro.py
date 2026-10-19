"""Video introductorio de Git (en inglés): commits, branches, HEAD,
viajes en el tiempo y detached HEAD.

Ejecutar:
    uv run manim -pql git_intro.py GitIntro    # vista rápida
    uv run manim -pqh git_intro.py GitIntro    # calidad alta
"""

import textwrap

from manim import *

MONO = "Consolas"
PANEL_BG = "#1e1e1e"

# Geometría del grafo
LANE_Y = {0: 0.0, 1: -1.7}          # carril 0 = línea principal, 1 = ramas
REF_DIR = {0: UP, 1: DOWN}           # hacia dónde se apilan las etiquetas
X0, DX = -6.0, 1.5                   # x del primer commit y separación
NODE_R = 0.32

BRANCH_COLORS = {"main": BLUE_C, "feature": GREEN_C, "experiment": PURPLE_B}
HEAD_COLOR = YELLOW
DETACHED_COLOR = RED_C

READING_SPEED = 3.0  # palabras por segundo al calcular pausas de lectura


def make_tag(text, color):
    label = Text(text, font_size=18, weight=BOLD, color=BLACK)
    box = RoundedRectangle(corner_radius=0.08, width=label.width + 0.3, height=0.4,
                           fill_color=color, fill_opacity=1, stroke_width=0)
    return VGroup(box, label)


class GitIntro(Scene):
    # ------------------------------------------------------------------ estado
    def setup(self):
        self.commits = {}       # id -> dict(node, arrow, pos, lane, files, hash)
        self.branches = {}      # nombre -> id de commit
        self.head = "main"      # nombre de branch (attached) o id de commit (detached)
        self.tags = {}          # nombre de ref -> mobject
        self.shown = set()      # refs que ya se presentaron en pantalla
        self.wd = []            # líneas actuales del working directory
        self.caption = VMobject()
        self.cmd_text = VMobject()
        self.chapter_label = VMobject()

    def detached(self):
        return self.head not in self.branches

    def head_commit(self):
        return self.head if self.detached() else self.branches[self.head]

    # ------------------------------------------------------------ utilidades
    def say(self, text, t2c=None, extra=0.0):
        """Muestra una explicación en la columna derecha y espera a que se lea."""
        new = Text(textwrap.fill(text, 34), font_size=24, line_spacing=1.1,
                   color=GREY_A, t2c=t2c or {})
        if new.width > 5.6:
            new.scale_to_fit_width(5.6)
        new.next_to(self.files_frame, DOWN, buff=0.4).align_to(self.files_frame, LEFT)
        self.play(FadeOut(self.caption), FadeIn(new), run_time=0.5)
        self.caption = new
        self.wait(len(text.split()) / READING_SPEED + extra)

    def run(self, cmd):
        """Escribe un comando en la barra de terminal."""
        new = Text(cmd, font=MONO, font_size=24).next_to(self.prompt, RIGHT, buff=0.2)
        self.play(FadeOut(self.cmd_text), run_time=0.2)
        self.play(AddTextLetterByLetter(new, run_time=max(0.5, 0.035 * len(cmd))))
        self.cmd_text = new

    def chapter(self, title):
        big = Text(title, font_size=56, weight=BOLD)
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                       fill_color=BLACK, fill_opacity=0.92, stroke_width=0)
        self.play(FadeIn(bg), FadeIn(big, scale=1.2), run_time=0.6)
        self.wait(0.8)
        small = Text(title, font_size=22, color=GREY_B).to_corner(UL, buff=0.25)
        self.play(FadeOut(bg), ReplacementTransform(big, small),
                  FadeOut(self.chapter_label), run_time=0.7)
        self.chapter_label = small

    def set_files(self, lines, mark_new=False):
        """Animaciones para cambiar el contenido de story.txt."""
        if lines:
            new = VGroup(*[
                Text(l, font=MONO, font_size=22,
                     color=YELLOW_B if mark_new and l not in self.wd else WHITE)
                for l in lines
            ]).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        else:
            new = Text("(empty)", font=MONO, font_size=22, color=GREY_C)
        new.next_to(self.files_header, DOWN, buff=0.35).align_to(self.files_header, LEFT)
        anims = [FadeOut(self.file_lines), FadeIn(new)]
        self.file_lines, self.wd = new, list(lines)
        return anims

    def edit(self, lines):
        self.play(*self.set_files(lines, mark_new=True))

    # ----------------------------------------------------------- referencias
    def ref_targets(self):
        """Posición de cada etiqueta (branches y HEAD) según el estado actual."""
        targets, by_commit = {}, {}
        for name, c in self.branches.items():
            if name in self.shown:
                by_commit.setdefault(c, []).append(name)
        for c, names in by_commit.items():
            names.sort(key=lambda n: n == self.head)  # la branch de HEAD va afuera
            info = self.commits[c]
            d = REF_DIR[info["lane"]]
            for k, n in enumerate(names):
                targets[n] = info["pos"] + d * (0.75 + 0.6 * k)
            if self.head in names:
                targets["HEAD"] = targets[self.head] + d * 0.75
        if self.detached():
            info = self.commits[self.head]
            k = len(by_commit.get(self.head, []))
            targets["HEAD"] = info["pos"] + REF_DIR[info["lane"]] * (0.75 + 0.6 * k)
        return {n: p for n, p in targets.items() if n in self.shown}

    def ref_anims(self):
        anims = []
        for name, p in self.ref_targets().items():
            if name not in self.tags:
                color = HEAD_COLOR if name == "HEAD" else BRANCH_COLORS[name]
                self.tags[name] = make_tag(name, color).move_to(p)
                anims.append(FadeIn(self.tags[name], scale=0.5))
                continue
            mob = self.tags[name]
            mob.generate_target()
            mob.target.move_to(p)
            if name == "HEAD":
                mob.target[0].set_fill(DETACHED_COLOR if self.detached() else HEAD_COLOR)
            anims.append(MoveToTarget(mob))
        return anims

    def head_arrow(self):
        head = self.tags["HEAD"]
        target = (self.commits[self.head]["node"] if self.detached()
                  else self.tags[self.head])
        if target.get_y() < head.get_y():
            start, end = head.get_bottom(), target.get_top()
        else:
            start, end = head.get_top(), target.get_bottom()
        if np.linalg.norm(end - start) < 0.1:
            return VMobject()
        return Arrow(start, end, buff=0.04, stroke_width=3, tip_length=0.12,
                     max_tip_length_to_length_ratio=0.6,
                     color=head[0].get_fill_color())

    # ------------------------------------------------------------- acciones git
    def git_commit(self, cid, msg, slot, lane, hash_, cmd=None):
        parent = self.head_commit() if self.commits else None
        self.run(cmd or f'git commit -am "{msg}"')

        pos = np.array([X0 + DX * slot, LANE_Y[lane], 0])
        node = VGroup(
            Circle(NODE_R, color=WHITE, stroke_width=3, fill_color=GREY_E, fill_opacity=1),
            Text(cid, font_size=20),
        ).move_to(pos)
        anims = [GrowFromCenter(node)]
        arrow = None
        if parent:
            arrow = Arrow(pos, self.commits[parent]["pos"], buff=NODE_R + 0.04,
                          stroke_width=3, tip_length=0.15, color=GREY_B)
            anims.insert(0, GrowArrow(arrow))
        self.commits[cid] = dict(node=node, arrow=arrow, pos=pos, lane=lane,
                                 files=list(self.wd), hash=hash_)
        if self.detached() and parent:
            self.head = cid
        else:
            self.branches[self.head] = cid
        self.play(*anims, *self.ref_anims(), self.file_lines.animate.set_color(WHITE))

    def checkout(self, target, cmd):
        """Mueve HEAD a una branch o a un commit y actualiza los archivos."""
        self.run(cmd)
        self.head = target
        self.play(*self.ref_anims(),
                  *self.set_files(self.commits[self.head_commit()]["files"]))

    def flash_hash(self, cid):
        info = self.commits[cid]
        h = Text(info["hash"], font=MONO, font_size=18, color=YELLOW)
        h.next_to(info["node"], DOWN if info["lane"] == 0 else UP, buff=0.12)
        self.play(FadeIn(h, shift=UP * 0.1), Indicate(info["node"], color=YELLOW))
        return h

    # =============================================================== guion
    def construct(self):
        self.intro()
        self.build_layout()
        self.part_commits()
        self.part_branches()
        self.part_head()
        self.part_time_travel()
        self.part_detached()
        self.part_right_way()
        self.recap()

    def intro(self):
        title = Text("Git, Visually", font_size=64, weight=BOLD)
        sub = Text("Commits, branches, HEAD and time travel", font_size=30, color=GREY_A)
        VGroup(title, sub).arrange(DOWN, buff=0.4)
        self.play(Write(title), run_time=1.2)
        self.play(FadeIn(sub, shift=UP * 0.2))
        self.wait(2)
        self.play(FadeOut(title, sub))

    def build_layout(self):
        self.bar = RoundedRectangle(width=13.6, height=0.6, corner_radius=0.1,
                                    fill_color=PANEL_BG, fill_opacity=1,
                                    stroke_color=GREY_D).move_to([0, 2.95, 0])
        self.prompt = Text("$", font=MONO, font_size=24, color=GREEN_C)
        self.prompt.move_to(self.bar).align_to(self.bar, LEFT).shift(RIGHT * 0.25)

        self.files_frame = RoundedRectangle(width=5.6, height=2.9, corner_radius=0.15,
                                            fill_color=PANEL_BG, fill_opacity=1,
                                            stroke_color=GREY_D).move_to([3.9, 0.95, 0])
        self.files_header = Text("story.txt", font=MONO, font_size=20, color=GREY_B)
        self.files_header.align_to(self.files_frame, UL).shift(RIGHT * 0.3 + DOWN * 0.25)
        wd_label = Text("working directory", font_size=16, color=GREY_C, slant=ITALIC)
        wd_label.align_to(self.files_frame, UR).shift(LEFT * 0.3 + DOWN * 0.27)
        self.file_lines = VMobject()
        empty = self.set_files([])

        self.play(FadeIn(self.bar, self.prompt, self.files_frame, self.files_header,
                         wd_label), *empty)

    # --------------------------------------------------------- 1. commits
    def part_commits(self):
        self.chapter("1. Commits")
        self.say("Git saves the history of your project as a chain of snapshots "
                 "called commits.")

        self.edit(["# My Story"])
        self.say("Let's write the first line of a story. Yellow means: changed, "
                 "but not saved yet.", t2c={"Yellow": YELLOW_B})
        self.run("git add story.txt")
        self.say("git add stages the changes we want to save.")

        self.git_commit("C1", "Add title", slot=0, lane=0, hash_="a1f9e2c",
                        cmd='git commit -m "Add title"')
        self.say("A commit is a snapshot of all your files at that moment, "
                 "plus a message and an author.")
        h = self.flash_hash("C1")
        self.say("Each commit has a unique ID called a hash. We'll call them "
                 "C1, C2... to keep it simple.", t2c={"hash.": YELLOW})
        self.play(FadeOut(h))

        self.edit(["# My Story", "Once upon a tme..."])
        self.git_commit("C2", "Add intro", slot=1, lane=0, hash_="7b3d0e4")
        self.say("Every new commit points back to its parent. "
                 "That chain of arrows IS your history.")

    # -------------------------------------------------------- 2. branches
    def part_branches(self):
        self.chapter("2. Branches")
        self.shown.add("main")
        self.play(*self.ref_anims())
        self.say("A branch is just a label that points to a commit. "
                 "The default one is called main.", t2c={"main.": BLUE_C})

        self.edit(["# My Story", "Once upon a tme...", "Ch1: The journey"])
        self.git_commit("C3", "Add chapter 1", slot=2, lane=0, hash_="e58c1a9")
        self.say("When you commit, the branch label moves forward automatically.")

        self.run("git branch feature")
        self.branches["feature"] = self.head_commit()
        self.shown.add("feature")
        self.play(*self.ref_anims())
        self.say("Creating a branch is instant: Git only adds a new label. "
                 "No files are copied.", t2c={"feature": GREEN_C})

    # ------------------------------------------------------------ 3. HEAD
    def part_head(self):
        self.chapter("3. HEAD")
        self.shown.add("HEAD")
        self.play(*self.ref_anims())
        self.head_arrow_mob = always_redraw(self.head_arrow)
        self.add(self.head_arrow_mob)
        self.say("So which branch are we on? Git tracks it with a special "
                 "pointer called HEAD.", t2c={"HEAD.": YELLOW})
        self.say("HEAD points to a branch, and the branch points to a commit. "
                 "HEAD means: you are here.", t2c={"HEAD": YELLOW})

        self.checkout("feature", "git switch feature")
        self.say("git switch moves HEAD to another branch.")

        self.edit(["# My Story", "Once upon a tme...", "Ch1: The journey",
                   "Ch2: A storm (draft)"])
        self.git_commit("F1", "Draft chapter 2", slot=3, lane=1, hash_="9d2e6f1")
        self.say("New commits now move feature forward, carrying HEAD along. "
                 "main stays where it was.",
                 t2c={"feature": GREEN_C, "main": BLUE_C, "HEAD": YELLOW})

    # ----------------------------------------------------- 4. time travel
    def part_time_travel(self):
        self.chapter("4. Time Travel")
        self.say("Moving HEAD is how you travel in time: your files change to "
                 "match the commit HEAD points to.", t2c={"HEAD": YELLOW})

        # Ejemplo 1: cambiar de branch
        self.checkout("main", "git switch main")
        self.say("Example 1: switch branches. The chapter 2 draft vanished "
                 "from our file... but it's safe in feature.",
                 t2c={"Example 1:": YELLOW, "feature.": GREEN_C})

        self.edit(["# My Story", "Once upon a time...", "Ch1: The journey"])
        self.git_commit("C4", "Fix typo", slot=3, lane=0, hash_="3c7f9b2")
        self.say("Back on main we fix a typo. History now splits into two lines.")

        # Ejemplo 2: posición relativa
        self.checkout("C2", "git checkout HEAD~2")
        self.say("Example 2: HEAD~2 means two commits before HEAD. "
                 "Look: the typo is back. We're in the past!",
                 t2c={"Example 2:": YELLOW, "HEAD~2": YELLOW})

        # Ejemplo 3: por hash
        self.run("git checkout a1f9e2c")
        h = self.flash_hash("C1")
        self.head = "C1"
        self.play(*self.ref_anims(), *self.set_files(self.commits["C1"]["files"]))
        self.say("Example 3: jump straight to any commit using its hash.",
                 t2c={"Example 3:": YELLOW})
        self.play(FadeOut(h))

    # --------------------------------------------------- 5. detached HEAD
    def part_detached(self):
        self.chapter("5. Detached HEAD")
        self.say("Notice HEAD turned red. It points directly to a commit, "
                 "not to a branch. This is called detached HEAD.",
                 t2c={"red.": DETACHED_COLOR, "detached": DETACHED_COLOR})
        self.say("It's perfect for looking around. But what if we make changes "
                 "and commit here?")

        self.edit(["# My Story", "It was a dark night"])
        self.git_commit("X1", "New opening", slot=1, lane=1, hash_="f04b8a7")
        self.say("The commit is created, but no branch points to it. "
                 "Only HEAD knows where it is.", t2c={"HEAD": DETACHED_COLOR})

        ghost = self.commits["X1"]
        self.checkout("main", "git switch main")
        self.play(ghost["node"].animate.set_opacity(0.25),
                  ghost["arrow"].animate.set_opacity(0.25))
        self.say("Switch away, and nothing points to it anymore. It's orphaned, "
                 "and Git will eventually delete it.",
                 t2c={"orphaned,": DETACHED_COLOR})
        self.play(FadeOut(ghost["node"], ghost["arrow"]))
        del self.commits["X1"]

    # ------------------------------------------------ 6. guardar bien
    def part_right_way(self):
        self.chapter("6. Saving Work the Right Way")
        self.say("The fix is simple: create a branch before you commit.")

        self.checkout("C1", "git checkout a1f9e2c")
        self.run("git switch -c experiment")
        self.branches["experiment"] = "C1"
        self.head = "experiment"
        self.shown.add("experiment")
        self.play(*self.ref_anims())
        self.say("git switch -c creates a new branch right here and moves HEAD "
                 "onto it. HEAD is attached again.",
                 t2c={"HEAD": YELLOW, "experiment": PURPLE_B})

        self.edit(["# My Story", "It was a dark night"])
        self.git_commit("X1", "New opening", slot=1, lane=1, hash_="f04b8a7")
        self.say("Now the commit belongs to experiment.",
                 t2c={"experiment.": PURPLE_B})

        self.checkout("main", "git switch main")
        self.say("Switch away and come back any time: nothing gets lost.")
        self.say("Already committed in detached HEAD? Rescue it before leaving "
                 "with: git branch <name>", t2c={"git branch <name>": YELLOW})

    # ---------------------------------------------------------- resumen
    def recap(self):
        # Fundido a negro tapando todo (más robusto que FadeOut del always_redraw)
        cortina = Rectangle(width=config.frame_width, height=config.frame_height,
                            fill_color=BLACK, fill_opacity=1, stroke_width=0)
        self.play(FadeIn(cortina))
        self.clear()
        title = Text("Recap", font_size=48, weight=BOLD).to_edge(UP, buff=0.5)
        rows = [
            ("commit", "a snapshot of your files + a link to its parent"),
            ("branch", "a movable label pointing to a commit"),
            ("HEAD", "where you are right now"),
            ("git switch <branch>", "travel to a branch"),
            ("git checkout <hash>", "travel to any commit (detached HEAD)"),
            ("git checkout HEAD~n", "go back n commits (detached HEAD)"),
            ("git switch -c <name>", "save your work on a new branch"),
        ]
        table = VGroup()
        for i, (left, right) in enumerate(rows):
            l = Text(left, font=MONO, font_size=24, color=YELLOW if i > 2 else BLUE_B)
            r = Text(right, font_size=24, color=GREY_A)
            l.move_to([-6.2, 0, 0], aligned_edge=LEFT)
            r.move_to([-1.2, 0, 0], aligned_edge=LEFT)
            table.add(VGroup(l, r))
        table.arrange(DOWN, buff=0.35, aligned_edge=LEFT).next_to(title, DOWN, buff=0.6)
        table.set_x(0)
        rule = Text("Golden rule: never commit in detached HEAD without a branch.",
                    font_size=26, color=YELLOW).to_edge(DOWN, buff=0.5)

        self.play(Write(title))
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in table],
                              lag_ratio=0.3), run_time=3)
        self.wait(6)
        self.play(Write(rule))
        self.wait(4)
