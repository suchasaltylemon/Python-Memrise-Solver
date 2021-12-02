from requests_futures.sessions import FuturesSession
from uuid import uuid4
from bs4 import BeautifulSoup
from json import loads
from re import compile

CSRF_PATTERN = compile("csrftoken: \"(.+)\"")

gen_url = lambda route: f"https://app.memrise.com{route}garden/classic_review/" + \
	"?source_element=course_mode&source_screen=course_details"

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


	def _course_csrf(self, course):
		route = course['url']

		res = self.session.get(f"https://app.memrise.com{route}garden/classic_review/",
			headers={
				"x-csrftoken": None
			}).result()

		token = CSRF_PATTERN.findall(res.text)[0]

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


	def course_info(self, course):
		info = loads(
			self.session.get(
				f"https://app.memrise.com/ajax/session/?course_id={course['id']}" + \
					 f"&course_slug={course['slug']}&session_slug=classic_review"
			).result().text
		)

		return info


	def solve(self, course, limit=None):
		self._course_csrf(course)

		info = self.course_info(course)

		route = course["url"]

		course_id = info["session"]["course_id"]

		screens = info["screens"].items()

		points = 200
		count = len(screens)
		max_points = count * 200 # Hard limit for max points is 200. Default for points is hard limit

		rem = 0
		if limit is not None and limit < max_points:
			points = limit // count
			rem = limit % count

		for i, (learnable_id, screen) in enumerate(screens):
			# Question
			q = list(
				filter(lambda v: v["template"] == "multiple_choice", \
					screen.values()
				)
			)[0]

			def_element = q["prompt"]["text"]["value"]
			correct_answer = q["correct"][0]
			learning_element = def_element

			data = {
				"box_template": "multiple_choice",
				"course_id": course_id,
				"definition_element": def_element,
				"fully_grow": False,
				"given_answer": correct_answer,
				"learnable_id": learnable_id,
				"learning_element": learning_element,
				"points": points if i != count - 1 else points + rem,
				"score": 1,
				"test_id": str(uuid4()),
				"time_spent": 2
			}

			x = self.session.post("https://app.memrise.com/ajax/learning/register",
				json=data,
				headers={
					"referer": gen_url(route)
				}
			)
