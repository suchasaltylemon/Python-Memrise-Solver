from json import load
from getpass import getpass

from lib.memrise import MemriseSession

def get_auth():
	un = pwd = None

	choice = input("Load auth from auth.json?\n y/n: ").lower().strip()

	if choice == "y":
		with open("./auth.json", "r") as fs:
			auth = load(fs)

			un, pwd = auth["username"], auth["password"]

	else:
		un = input("Username: ")
		pwd = getpass("Password: ")

	return un, pwd

def choose_course(courses):
	size = len(courses)

	choice = None
	while choice is None:
		for i, course in enumerate(courses):
			print(f"{i + 1}) {course['name']}")

		try:
			index = int(input("\n > "))

		except ValueError:
			continue

		else:
			if 0 < index <= size:
				choice = courses[index - 1]

	return choice

def main():
	input()
	un, pwd = get_auth()

	with MemriseSession(un, pwd) as ms:
		courses = [course for chunk in ms.courses() for course in chunk]

		choice = choose_course(courses)


if __name__ == "__main__":
	main()

