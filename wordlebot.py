import discord
import logging
import random
import json
import os
from discord import app_commands
from dotenv import load_dotenv

#-----------------------------------------------

# Initialize Discord Bot Configurations
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID_1 = os.getenv("GUILD_ID_1")

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Initialize Discord Guilds
guilds = []

with open('guilds.json', 'r') as file:
    guild_ids = json.load(file)

for guild_id in guild_ids:
    guilds.append(discord.Object(guild_id))

# Initialize Logging Configurations
logging.basicConfig(
    filename="wordlebot.log",
    encoding="utf-8",
    filemode="w",
    format="{asctime} - {levelname} : {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

#-----------------------------------------------

CURRENT_WORD: str = None
REMAINING_TRIES: int

@client.event
async def on_ready() -> None:
    """
    Called when the Discord bot is ready to be used.
    """
    logging.info(f"{client.user} has connected to Discord.")
    logging.info(f"Close the terminal to disconnect {client.user}.") 


@app_commands.checks.has_permissions(administrator=True)
@tree.command(name="sync", description="Syncs Wordle Bot Commands. Must have administrator permission to use.", guilds=guilds)
async def Sync(interaction: discord.Interaction) -> None:
    """
    Syncs the commands in the script to Discord's servers.

    This must be run through Discord after any code changes have been made.

    Args:
        interaction (discord.Interaction): The connection between the bot and the user.
    """

    user: str = interaction.user.display_name
    logging.debug(f"Received SYNC command by {user}.")

    try:

        embed: discord.Embed = discord.Embed(
            title = "Syncing Commands...",
            description = f"Total Guilds: {len(guilds)}",
            color = discord.Color.yellow()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Begin syncing and update status to user
        for index, guild in enumerate(guilds):

            embed.add_field(name=guild.id, value="In Progress...")
            await interaction.edit_original_response(embed=embed)
            logging.debug(f"Syncing Guild: {guild.id}")

            await tree.sync(guild=guild)

            embed.set_field_at(index=index, name=guild.id, value="Synced!")
            await interaction.edit_original_response(embed=embed)
            logging.debug(f"Finished Syncing Guild: {guild.id}")

        # Update status when complete
        embed.set_footer(text="Syncing Complete!")
        await interaction.edit_original_response(embed=embed)

    except Exception as Ex:
        logging.error(Ex)
    
    logging.debug(f"Completed SYNC command by {user}.")


@tree.command(name="startgame", description="Starts a new Wordle game.", guilds=guilds)
async def StartGame(interaction: discord.Interaction) -> None:
    """
    Processes a '/startgame' command in Discord.

    This function chooses a random word from the words.json file and creates a new Wordle game.

    Args:
        interaction (discord.Interaction): The connection between the bot and the user.
    """

    user: str = interaction.user.display_name
    logging.debug(f"Received STARTGAME command by {user}.")
    global CURRENT_WORD
    global REMAINING_TRIES

    try:

        # Check if a game is already active
        if CURRENT_WORD is not None:
            await interaction.response.send_message("There is already a game going on!")
            logging.debug(f"Cancelled STARTGAME command by {user}. Reason: There is already an active game.")
            return

        # Load the words file and choose a random word
        with open('words.json', 'r') as file:
            words = json.load(file)

        random_index = random.randint(0, len(words) - 1)
        CURRENT_WORD = words[random_index].lower()
        REMAINING_TRIES = 6
        logging.info(f"Creating new Wordle game using: {CURRENT_WORD}")

        embed: discord.Embed = discord.Embed(
            title = "A new Wordle game has been created!",
            description = "Type '/guess' to start playing!",
            color = discord.Color.yellow()
        )

        await interaction.response.send_message(embed=embed)
        
    except Exception as Ex:
        logging.error(Ex)

    logging.debug(f"Completed STARTGAME command by {interaction.user.display_name}.")


@tree.command(name="guess", description="Submits a Wordle guess.", guilds=guilds)
async def Guess(interaction: discord.Interaction, attempt: str) -> None:
    """
    Processes a '/guess' command in Discord.

    This function checks the user's guess and uses emojis to display feedback.

    If the guess is correct, the game displays the winner. Otherwise, the amount of remaining tries is decremented.

    If there are no more remaining tries, the game ends in a loss.

    Args:
        interaction (discord.Interaction): The connection between the bot and the user.
        attempt (str): The user's Wordle guess.
    """

    user: str = interaction.user.display_name
    logging.debug(f"Received GUESS command by {user}.")

    global CURRENT_WORD
    global REMAINING_TRIES

    try:

        # Check for active game
        if CURRENT_WORD is None:
            await interaction.response.send_message("There is no game going on right now. Type /startgame to start a new one!", ephemeral=True)
            logging.debug(f"Cancelled GUESS command by {user}. Reason: There is no active game.")
            return

        # Check for valid guess
        if len(attempt) != 5 or not attempt.isalpha():
            await interaction.response.send_message("Your guess must be a 5-letter word with only letters!", ephemeral=True)
            logging.debug(f"Cancelled GUESS command by {user}. Reason: Invalid guess input.")
            return

        attempt = list(attempt.lower())
        response: list[str] = ["", "", "", "", ""]

        for i in range(5):

            # Correct letter in correct spot
            if attempt[i] == CURRENT_WORD[i]:
                response[i] = ":green_square:"

            # Correct letter in wrong spot
            elif attempt[i] in CURRENT_WORD:
                response[i] = ":yellow_square:"

            # Incorrect letter
            else:
                response[i] = ":black_large_square:"

            attempt[i] = f":regional_indicator_{attempt[i]}:"

        REMAINING_TRIES -= 1

        # Create response to user
        embed: discord.Embed = discord.Embed(
            title = ' '.join(attempt),
            description = ' '.join(response),
            color  = discord.Color.yellow()
        )

        # If the answer is correct
        if response == [":green_square:"] * 5:

            logging.info(f"{user} has guessed the word!")
            embed.set_footer(text=f"{user} has guessed the word!")
            CURRENT_WORD = None

        # If there are no more tries
        elif REMAINING_TRIES == 0:

            logging.info(f"Ran out of attempts! The game is lost.")
            embed.set_footer(text=f"Ran out of attempts! The word was: {CURRENT_WORD}")
            CURRENT_WORD = None

        else:

            logging.info(f"Remaining Guesses: {REMAINING_TRIES}")
            embed.set_footer(text=f"Remaining Guesses: {REMAINING_TRIES}")

        await interaction.response.send_message(embed=embed)

    except Exception as Ex:
        logging.error(Ex)
    
    logging.debug(f"Completed GUESS command by {user}.")


client.run(BOT_TOKEN)