import re
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

class ShakespeareReader:
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.scenes: Dict[Tuple[int, int], str] = {}
        self.console = Console()
        self.play_name = self._get_play_name()
        self._parse_play()

    def _get_play_name(self) -> str:
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                return first_line if first_line else "Unknown Play"
        except Exception:
            return "Unknown Play"

    def _parse_play(self):
        """Parse the play file and extract all acts and scenes."""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_act = None
        current_scene = None
        scene_content = []

        for line in lines:
            # Check for ACT marker
            act_match = re.match(r'^ACT (\d+)$', line.strip())
            if act_match:
                # Save previous scene before changing act
                if current_act is not None and current_scene is not None:
                    self.scenes[(current_act, current_scene)] = ''.join(scene_content)

                current_act = int(act_match.group(1))
                current_scene = None
                scene_content = []
                continue

            # Check for Scene marker
            scene_match = re.match(r'^Scene (\d+)$', line.strip())
            if scene_match:
                # Save previous scene if exists
                if current_act is not None and current_scene is not None:
                    self.scenes[(current_act, current_scene)] = ''.join(scene_content)

                # Start new scene
                current_scene = int(scene_match.group(1))
                scene_content = []
                continue

            # Collect scene content (skip the ===== separators)
            if current_act is not None and current_scene is not None:
                if not re.match(r'^=+$', line.strip()):
                    scene_content.append(line)

        # Save the last scene
        if current_act is not None and current_scene is not None:
            self.scenes[(current_act, current_scene)] = ''.join(scene_content)

    def get_scene(self, act: int, scene: int) -> Optional[str]:
        """Get the text for a specific act and scene."""
        return self.scenes.get((act, scene))

    def format_scene_text(self, text: str) -> Text:
        """Format scene text with styles for character names and stage directions."""
        rich_text = Text(text)

        # Find all bracketed content (stage directions)
        bracket_spans = []
        for match in re.finditer(r'\[([^\]]*?)\]', text):
            bracket_spans.append((match.start(), match.end()))
            rich_text.stylize("italic plum2", match.start(), match.end())

        # Find all fully capitalized words (character names)
        # Only style them if they're not inside brackets
        for match in re.finditer(r'\b([A-Z]{2,})\b', text):
            # Check if this match overlaps with any bracket span
            overlaps = any(
                match.start() >= b_start and match.end() <= b_end
                for b_start, b_end in bracket_spans
            )
            if not overlaps:
                rich_text.stylize("bold orange1", match.start(), match.end())

        return rich_text

    def display_scene(self, act: int, scene: int):
        """Display a scene with Rich formatting."""
        scene_text = self.get_scene(act, scene)

        if scene_text is None:
            self.console.print(
                Panel(
                    f"[bold red]Act {act}, Scene {scene} not found![/bold red]\n\n"
                    f"Available acts: 1-5\n"
                    f"Please check your input.",
                    title="Error",
                    border_style="red"
                )
            )
            return

        # Format the scene text with styles
        formatted_text = self.format_scene_text(scene_text.strip())

        # Create a nice header
        title = f"[bold cyan]{self.play_name} - Act {act}, Scene {scene}[/bold cyan]"

        # Display in a panel
        self.console.print()
        self.console.print(
            Panel(
                formatted_text,
                title=title,
                border_style="cyan",
                padding=(1, 2),
                width=80,
                expand=False
            )
        )
        self.console.print()

    def parse_dialogues(self, scene_text: str) -> List[str]:
        """Parse a scene into individual dialogues/speeches."""
        dialogues = []
        lines = scene_text.strip().split('\n')
        current_dialogue = []

        for line in lines:
            # Check if line starts with a character name (2+ consecutive caps)
            # Character names usually appear at start of line or after whitespace
            if re.match(r'^[A-Z]{2,}(\s+[A-Z]+)*\s*$', line.strip()) or \
               re.match(r'^[A-Z]{2,}(\s+[A-Z]+)*\s+', line.strip()):
                # Save previous dialogue if exists
                if current_dialogue:
                    dialogues.append('\n'.join(current_dialogue))
                    current_dialogue = []

                # Start new dialogue with character name
                current_dialogue.append(line)
            else:
                # Continue current dialogue
                if current_dialogue or line.strip():  # Don't start with empty lines
                    current_dialogue.append(line)

        # Save last dialogue
        if current_dialogue:
            dialogues.append('\n'.join(current_dialogue))

        return dialogues

    def display_scene_dialogue_mode(self, act: int, scene: int):
        """Display a scene dialogue by dialogue with navigation."""
        scene_text = self.get_scene(act, scene)

        if scene_text is None:
            self.console.print(
                Panel(
                    f"[bold red]Act {act}, Scene {scene} not found![/bold red]\n\n"
                    f"Available acts: 1-5\n"
                    f"Please check your input.",
                    title="Error",
                    border_style="red"
                )
            )
            return

        dialogues = self.parse_dialogues(scene_text)

        if not dialogues:
            self.console.print("[yellow]No dialogues found in this scene.[/yellow]")
            return

        dialogue_index = 0

        while dialogue_index < len(dialogues):
            # Print header
            self.console.print(f"[bold cyan]{self.play_name} - Act {act}, Scene {scene} - Dialogue {dialogue_index + 1}/{len(dialogues)}[/bold cyan]\n")

            # Format and display current dialogue with left border
            formatted_text = self.format_scene_text(dialogues[dialogue_index])

            # Add vertical line to the left of each line
            lines = str(formatted_text).split('\n')
            for line in lines:
                self.console.print(f"[cyan]│[/cyan] {line}")

            self.console.print()

            # Prompt for next action
            action = Prompt.ask(
                "[dim](n/p/q)[/dim]",
                default=""
            ).strip().lower()

            if action == 'n':
                if dialogue_index < len(dialogues) - 1:
                    dialogue_index += 1
                else:
                    self.console.print("[yellow]End of scene. Press Enter to continue.[/yellow]")
                    Prompt.ask("", default="")
                    break
            elif action == 'p':
                if dialogue_index > 0:
                    dialogue_index -= 1
            elif action == 'q':
                break

    def list_available_scenes(self):
        """List all available act.scene combinations."""
        acts_dict: Dict[int, list] = {}
        for act, scene in sorted(self.scenes.keys()):
            if act not in acts_dict:
                acts_dict[act] = []
            acts_dict[act].append(scene)

        self.console.print("\n[bold]Available scenes:[/bold]")
        for act, scenes in sorted(acts_dict.items()):
            scene_range = f"1-{max(scenes)}" if len(scenes) > 1 else "1"
            self.console.print(f"  Act {act}: Scenes {scene_range}")
        self.console.print()


def main():
    console = Console()
    main_loop(console)


def main_loop(console):
    # Print welcome banner
    console.print()
    # List available plays
    from glob import glob
    import os
    # Get the data directory relative to this module
    data_dir = Path(__file__).parent / "data" / "folger-txt-mod"
    play_files = sorted(glob(str(data_dir / "*.txt")))
    if not play_files:
        console.print(f"[bold red]No plays found in {data_dir}![/bold red]")
        return
    console.print("[bold cyan]Available Plays:[/bold cyan]")
    for idx, pf in enumerate(play_files, 1):
        try:
            with open(pf, 'r', encoding='utf-8') as f:
                play_title = f.readline().strip()
        except Exception:
            play_title = os.path.basename(pf)
        console.print(f"  [yellow]{idx}[/yellow]: {play_title}")
    console.print()
    selected = None
    while selected is None:
        sel = Prompt.ask("Enter play number to select (or 'q' to quit)", default="1")
        if sel.strip().lower() in ['quit', 'exit', 'q']:
            console.print("\n[dim]Goodbye![/dim]\n")
            return
        try:
            sel_idx = int(sel)
            if 1 <= sel_idx <= len(play_files):
                selected = play_files[sel_idx-1]
            else:
                console.print("[red]Invalid selection.[/red]")
        except Exception:
            console.print("[red]Invalid input.[/red]")
    # Print welcome banner
    console.print(Panel.fit(
        f"[bold cyan]{ShakespeareReader(selected)._get_play_name()}[/bold cyan]\n"
        "[dim]Interactive Scene Reader[/dim]\n\n"
        "Enter [yellow]x.y[/yellow] to read Act x, Scene y\n"
        "Enter [yellow]list[/yellow] to see available scenes\n"
        "Enter [yellow]mode[/yellow] to toggle dialogue-by-dialogue mode\n"
        "Enter [yellow]quit[/yellow] or [yellow]exit[/yellow] to quit",
        border_style="cyan"
    ))
    console.print()

    # Initialize reader
    text_file = selected
    try:
        reader = ShakespeareReader(text_file)
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] Could not find {text_file}")
        console.print("Make sure you're running this from the project root directory.")
        return

    # Mode tracking
    dialogue_mode = False

    # REPL loop
    while True:
        try:
            # Show current mode in prompt
            mode_indicator = "[yellow](dialogue mode)[/yellow] " if dialogue_mode else ""
            user_input = Prompt.ask(
                f"[bold green]{mode_indicator}Enter Act.Scene[/bold green]",
                default=""
            ).strip().lower()

            if user_input in ['quit', 'exit', 'q']:
                console.print("\n[dim]Goodbye![/dim]\n")
                return

            if not user_input:
                continue

            if user_input == 'list':
                reader.list_available_scenes()
                continue

            if user_input == 'mode':
                dialogue_mode = not dialogue_mode
                mode_status = "enabled" if dialogue_mode else "disabled"
                console.print(f"[bold cyan]Dialogue-by-dialogue mode {mode_status}[/bold cyan]")
                continue

            # Parse x.y format
            match = re.match(r'^(\d+)\.(\d+)$', user_input)
            if not match:
                console.print(
                    "[yellow]Invalid format. Please enter as x.y (e.g., 1.2 for Act 1, Scene 2)[/yellow]"
                )
                continue

            act = int(match.group(1))
            scene = int(match.group(2))

            # Display based on mode
            if dialogue_mode:
                reader.display_scene_dialogue_mode(act, scene)
            else:
                reader.display_scene(act, scene)

        except KeyboardInterrupt:
            console.print("\n\n[dim]Goodbye![/dim]\n")
            return
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    main()
