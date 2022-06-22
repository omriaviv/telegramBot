from setuptools import setup, find_packages

setup(
    name='pyTelegramPokerBot',
    version='0.1.0',
    author='Omri Aviv',
    author_email='omriaviv@microsoft.com',
    packages=find_packages(),
    url='https://github.com/omriaviv/telegramBot',
    description='Telegram Bot for Poker with friends',
    install_requires=[
        "pyTelegramBotAPI",
        "tinydb"
    ]
)
