from requests_futures.sessions import FuturesSession
from bs4 import BeautifulSoup
from json import loads

class MemriseSession:
	def __enter__(self):
		return self

	def __exit__(self, *_):
		self.close()

	def __init__(self, username, password):
		self.session = FuturesSession()

		self.session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" + \
			"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"
		self.session.headers["X-Requested-With"] = "XMLHttpRequest"

		self._login(username, password)


	def _oauth(self):
		page = self.session.get("https://app.memrise.com/signin")

		soup = BeautifulSoup(page.result().text, "html.parser")
		script = soup.find("script", {"id": "__NEXT_DATA__"})
		content = loads(script.contents[0])

		oauth = content["runtimeConfig"]["OAUTH_CLIENT_ID"]

		return oauth


	def _login_csrf(self):
		page = self.session.get(
			"https://app.memrise.com/v1.17/web/ensure_csrf")

		token = loads(page.result().text)["csrftoken"]

		self.session.headers["x-csrftoken"] = token


	def _login(self, username, password):
		res = self.session.post("https://app.memrise.com/v1.17/auth/access_token/", json={
			"username": username, "password": password, "grant_type": "password",
			"client_id": self._oauth()
		})

		token = loads(res.result().text)["access_token"]["access_token"]

		self.session.get(f"https://app.memrise.com/v1.17/auth/web/?invalidate_token_after=true&token={token}").result()


	def courses(self):
		offset = 0
		limit = 4

		finished = False

		while not finished:
			res = self.session.get(
				f"https://app.memrise.com/ajax/courses/dashboard/?courses_filter=most_recent&offset={offset * limit}" + \
					f"&limit={limit}"
			)

			body = loads(res.result().text)
			offset += 1
			finished = not body["has_more_courses"]

			yield body["courses"]


	def close(self):
		self.session.close()
