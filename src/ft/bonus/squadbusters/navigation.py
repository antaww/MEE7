import discord

from src.utilities.settings import Settings

settings = Settings()


class NavigationView(discord.ui.View):
    def __init__(self, characters, abilities_data, start_index=0):
        super().__init__(timeout=None)
        self.characters = characters
        self.abilities_data = abilities_data
        self.current_index = start_index

    def update_embed(self):
        character = self.characters[self.current_index]
        data = self.abilities_data[character]
        embed = discord.Embed(title="Ultra Abilities",
                              description=self.abilities_data['description'],
                              color=0xfd6ce4)
        embed.add_field(name=data['name'], value=data['description'], inline=False)
        embed.add_field(name="Details", value=data['details'], inline=False)
        embed.set_image(url=data['image'])
        embed.set_footer(text=f"MEE7 Squad Busters Ultra Abilities | {self.current_index + 1}/{len(self.characters)}",
                         icon_url=settings.get('icon_url'))
        return embed

    @discord.ui.button(label='⬅️', style=discord.ButtonStyle.secondary)
    async def left(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_index = (self.current_index - 1) % len(self.characters)
        embed = self.update_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='➡️', style=discord.ButtonStyle.secondary)
    async def right(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_index = (self.current_index + 1) % len(self.characters)
        embed = self.update_embed()
        await interaction.response.edit_message(embed=embed, view=self)
