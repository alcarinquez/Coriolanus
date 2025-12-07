import re
import os
from pathlib import Path
from typing import Dict, Tuple, Optional, List

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.layout import Layout

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style


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
                # Remove " by William Shakespeare" suffix if present
                if first_line.endswith(" by William Shakespeare"):
                    first_line = first_line[:-len(" by William Shakespeare")]
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

        # Configure pager to support colors
        original_pager = os.environ.get('PAGER', '')
        os.environ['PAGER'] = 'less -R'

        try:
            # Display in a pager with color support
            with self.console.pager(styles=True):
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
        finally:
            # Restore original pager setting
            if original_pager:
                os.environ['PAGER'] = original_pager
            else:
                os.environ.pop('PAGER', None)

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


def clear_screen(console):
    """Clear the terminal screen and scrollback buffer."""
    import sys

    # Rich handles cross-platform clearing
    console.clear()

    # Bonus: try to clear scrollback (best effort)
    try:
        sys.stdout.write('\033[3J')
        sys.stdout.flush()
    except:
        pass  # Silently ignore if not supported


def corio_repl(console):
    # Clear terminal scrollback
    clear_screen(console)

    # Rich layout for homepage
    home_layout = Layout()
    home_layout.split_column(
        Layout(name="upper",size=5),
        Layout(name="lower", size=10)
    )
    home_layout["upper"].split_row(
        Layout(name="left", size=18),
        Layout(name="center", size=5),
        Layout(name="right", size=48)
    )
    home_layout["lower"].update(
        "Input the [bold]first letter[/bold] of any play title! (e.g. [indian_red]H/h[/indian_red] for [italic]Hamlet[/italic])\n"
        "Then press [sky_blue2]↑/↓[/sky_blue2] and [sky_blue2]↵ ENTER[/sky_blue2] to choose from the dropdown menu.\n\n\n"
        "Or enter one of the commands below:\n"
        "   [sky_blue2]list[/sky_blue2] to select from the entire catalogue of Shakespeare's works\n"
        "   [sky_blue2]rand[/sky_blue2] to read a random play\n\n\n"
        "To exit the app, enter [indian_red]q[/indian_red] or [sky_blue2]quit[/sky_blue2]."
    )
    home_layout["left"].update(
        "[bold][sky_blue2]Welcome to[/sky_blue2]\n[gold3]CORIOLANUS[/bold] v0.1.0[/gold3]\n"
        "[gold3]>>>[/gold3]"
    )
    home_layout["center"].update(
        "[gold3]  │  \n  │  \n  │  [/gold3]"
    )
    home_layout["right"].update(
        "[italic gold3]\"I had rather have one scratch my head i'th' sun\n"
        " When the alarum were struck than idly sit\n"
        " To hear my nothings monster'd.\"[/italic gold3]"
    )
    console.print(Panel(home_layout, border_style="gold3", width=79, height=19, padding=(1,3)))
    

    # List available plays
    from glob import glob
    import os
    # Get the data directory relative to this module
    data_dir = Path(__file__).parent / "data" / "plays"
    play_files = sorted(glob(str(data_dir / "*.txt")))
    if not play_files:
        console.print(f"[bold red]No plays found in {data_dir}![/bold red]")
        return

    # Build a mapping of play names to file paths
    play_map = {}
    for pf in play_files:
        try:
            with open(pf, 'r', encoding='utf-8') as f:
                play_title = f.readline().strip()
                # Remove " by William Shakespeare" suffix if present
                if play_title.endswith(" by William Shakespeare"):
                    play_title = play_title[:-len(" by William Shakespeare")]
        except Exception:
            play_title = os.path.basename(pf)
        play_map[play_title] = pf

    # Create autocompleter with play names (case-insensitive, match from beginning)
    play_completer = WordCompleter(
        list(play_map.keys()),
        ignore_case=True
    )

    # Create custom style with transparent background and no scrollbar
    custom_style = Style.from_dict({
        'prompt-symbol': 'fg:#d7af00',
        'completion-menu.completion': 'fg: ansigray bg:',
        'completion-menu.completion.current': 'fg:#d7af00 bg:',
        'scrollbar.background': 'bg:',
        'scrollbar.button': 'bg:',
    })

    selected = None
    while selected is None:
        try:
            sel = prompt(
                FormattedText([('class:prompt-symbol', '___\n>>> ')]),
                completer=play_completer,
                style=custom_style,
                complete_while_typing=True
            ).strip()
            console.print()  # Print newline after input
            if sel.lower() in ['quit', 'exit', 'q']:
                console.print("\n[dim]Goodbye![/dim]\n")
                return

            # Handle list command - show full catalogue
            if sel.lower() == 'list':
                # Create style for choice menu
                choice_style = Style.from_dict({
                    'selected-option': 'fg:#d7af00',  # Hovered/selected item
                    'number': 'fg: #87afff',           # Option numbers
                    'input-selection': '',            # Input selection area
                })

                # Add "0. Cancel" option at the beginning
                choice_options = [(None, "[Cancel selection]")] + [(name, name) for name in sorted(play_map.keys())]

                play_choice = choice(
                    message="Select a play from the complete catalogue:",
                    options=choice_options,
                    style=choice_style
                )
                if play_choice:  # If not None (not cancelled)
                    selected = play_map[play_choice]
                continue

            # Handle rand command - select random play
            if sel.lower() == 'rand':
                import random
                random_play = random.choice(list(play_map.keys()))
                console.print(f"[dim]Randomly selected:[/dim] [cyan]{random_play}[/cyan]")
                selected = play_map[random_play]
                continue

            # Match play name (case-insensitive)
            matched_play = None
            for play_name, play_path in play_map.items():
                if play_name.lower() == sel.lower():
                    matched_play = play_path
                    break

            if matched_play:
                selected = matched_play
            elif sel:
                console.print(" [indian_red]Play/Command not found. Please refer to usage above.[/indian_red]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]\n")
            return

    # Clear the screen and scrollback buffer
    clear_screen(console)

    # Print welcome banner for selected play
    console.print(Panel.fit(
        f"[bold gold3]{ShakespeareReader(selected)._get_play_name()}[/bold gold3]\n"
        "[italic dim gold3]by William Shakespeare[/italic dim gold3]\n\n"
        "Enter [sky_blue2]x.y[/sky_blue2] to read Act x, Scene y (e.g., [indian_red]1.1[/indian_red] for Act 1, Scene 1)\n"
        "Enter [sky_blue2]list[/sky_blue2] to see available scenes\n"
        "Enter [sky_blue2]mode[/sky_blue2] to toggle dialogue-by-dialogue mode\n"
        "Enter [sky_blue2]home[/sky_blue2] to return to play selection\n"
        "Enter [indian_red]quit[/indian_red] to exit",
        border_style="gold3",
        title="[italic gold3]Now reading[/italic gold3]",
        title_align="right"
    ))
    
    # Initialize reader
    text_file = selected
    try:
        reader = ShakespeareReader(text_file)
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] Could not find {text_file}")
        console.print("Make sure you're running this from the project root directory.")
        return

    # Mode tracking: "normal", "pager", or "dialogue"
    reading_mode = "pager"  # Default mode

    # REPL loop
    while True:
        try:
            # Show current mode in prompt
            mode_indicator = f"({reading_mode}) " if reading_mode != "pager" else ""
            user_input = prompt(
                FormattedText([
                    ('class:separator', '___\n'),
                    ('class:prompt-symbol', f'>>> {mode_indicator} ')
                ]),
                style=Style.from_dict({
                    'separator': 'fg:#d7af00',
                    'prompt-symbol': 'fg:#d7af00',
                })
            ).strip().lower()
            console.print()
            
            if user_input in ['quit', 'exit', 'q']:
                console.print("\n[dim]Goodbye![/dim]\n")
                return

            if not user_input:
                continue

            if user_input == 'list':
                reader.list_available_scenes()
                continue

            if user_input == 'mode':
                # Create style for mode selection
                mode_choice_style = Style.from_dict({
                    'selected-option': 'fg:#d7af00',
                    'number': 'fg:#87afff',
                    'input-selection': '',
                })

                # Mode selection menu
                mode_options = [
                    ("normal", "Normal - Display scene all at once"),
                    ("pager", "Pager - Scrollable view (default)"),
                    ("dialogue", "Dialogue - Navigate line by line")
                ]

                selected_mode = choice(
                    message="Select reading mode:",
                    options=mode_options,
                    style=mode_choice_style,
                    default=reading_mode
                )

                if selected_mode:
                    reading_mode = selected_mode
                    console.print(f"\n [gold3]Mode set to: {reading_mode}[/gold3]")
                continue

            if user_input == 'home':
                clear_screen(console)
                corio_repl(console)  # Recursively call to return to play selection
                return  # Exit current play session

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
            if reading_mode == "dialogue":
                reader.display_scene_dialogue_mode(act, scene)
            elif reading_mode == "pager":
                reader.display_scene(act, scene)
            else:  # normal mode
                # Display without pager - just print directly
                scene_text = reader.get_scene(act, scene)
                if scene_text is None:
                    console.print(
                        Panel(
                            f"[bold red]Act {act}, Scene {scene} not found![/bold red]\n\n"
                            f"Available acts: 1-5\n"
                            f"Please check your input.",
                            title="Error",
                            border_style="red"
                        )
                    )
                else:
                    formatted_text = reader.format_scene_text(scene_text.strip())
                    title = f"[bold cyan]{reader.play_name} - Act {act}, Scene {scene}[/bold cyan]"
                    console.print()
                    console.print(
                        Panel(
                            formatted_text,
                            title=title,
                            border_style="cyan",
                            padding=(1, 2),
                            width=80,
                            expand=False
                        )
                    )
                    console.print()

        except KeyboardInterrupt:
            console.print("\n\n[dim]Goodbye![/dim]\n")
            return
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


def main():
    console = Console()
    corio_repl(console)
    
    
if __name__ == "__main__":
    main()
