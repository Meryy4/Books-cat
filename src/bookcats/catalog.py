"""The corpus: each book is pinned to its Project Gutenberg ID.

Pinning IDs (instead of searching by title) avoids getting the wrong book,
e.g. a search for "The War of the Worlds" that returns another novel.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    key: str            # short identifier, used for file names
    title: str
    author: str
    year: int           # first publication
    gutenberg_id: int
    check_words: tuple[str, ...]  # words that must appear near the start of the text


BOOKS: list[Book] = [
    Book("alice", "Alice's Adventures in Wonderland", "Lewis Carroll", 1865, 11, ("Alice",)),
    Book("dracula", "Dracula", "Bram Stoker", 1897, 345, ("DRACULA",)),
    Book("frankenstein", "Frankenstein", "Mary Shelley", 1818, 84, ("Frankenstein",)),
    Book("dorian_gray", "The Picture of Dorian Gray", "Oscar Wilde", 1890, 174, ("Dorian Gray",)),
    Book("metamorphosis", "The Metamorphosis", "Franz Kafka", 1915, 5200, ("Metamorphosis", "Gregor")),
    Book("pride_prejudice", "Pride and Prejudice", "Jane Austen", 1813, 1342, ("Pride", "Prejudice")),
    Book("time_machine", "The Time Machine", "H. G. Wells", 1895, 35, ("Time Machine",)),
    Book("two_cities", "A Tale of Two Cities", "Charles Dickens", 1859, 98, ("TALE OF TWO CITIES",)),
    Book("war_worlds", "The War of the Worlds", "H. G. Wells", 1898, 36, ("War of the Worlds",)),
    Book("jungle_book", "The Jungle Book", "Rudyard Kipling", 1894, 236, ("JUNGLE BOOK",)),
]

BY_KEY = {b.key: b for b in BOOKS}
