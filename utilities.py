
# creates a progress bar
# credit: iambr, https://stackoverflow.com/questions/3160699/python-progress-bar
import sys
# give multiple completion rates (in fraction)
def progressbar(completion, completion2=None, size=50, time_remaining="99:99:99", text="Progress: ", text2="Scenarios: ", text3="Time remaining: "):
	x = int(size*completion)
	x2 = completion2
	sys.stdout.write("%s[%s%s] %02d %% | %s %02d %% | %s %s\r" % (text, "#"*x, "."*(size-x), completion*100, text2, completion2*100, text3, time_remaining))
	sys.stdout.flush()

#display progress as percentage
def display_progress(completion, text="Progress: "):
	sys.stdout.write("%s[%02d %%]\r" % (text, completion*100))
	sys.stdout.flush()

# for suppressing console output
# credit: charleslparker, https://stackoverflow.com/questions/2125702/how-to-suppress-console-output-in-python
import sys, os, contextlib
@contextlib.contextmanager
def suppress_stdout():
	with open(os.devnull, "w") as devnull:
		old_stdout = sys.stdout
		sys.stdout = devnull
		try:  
			yield
		finally:
			sys.stdout = old_stdout
# alternative solution
# credit: Alex Martelli, https://stackoverflow.com/questions/2828953/silence-the-stdout-of-a-function-in-python-without-trashing-sys-stdout-and-resto
import io
@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.BytesIO()
    yield
    sys.stdout = save_stdout
# another alternative
# credit: jfs and Yinon Ehrlich, https://stackoverflow.com/questions/5081657/how-do-i-prevent-a-c-shared-library-to-print-on-stdout-in-python
@contextlib.contextmanager
def stdout_redirected(to=os.devnull):
	fd = sys.stdout.fileno()
	def _redirect_stdout(to):
		sys.stdout.close()
		os.dup2(to.fileno(), fd)
		sys.stdout = os.fdopen(fd, 'w')
	with os.fdopen(os.dup(fd), 'w') as old_stdout:
		with open(to, 'w') as file:
			_redirect_stdout(to=file)
		try:
			yield
		finally:
			_redirect_stdout(to=old_stdout)

# print output in different colors
# available colors: 
def color_print(s, c=None):
	CSI = "\x1B["
	color_end = '\033[0m'
	colors = {"red": '\033[91m', "green": '\033[92m', "blue": '\033[94m', "yellow": '\033[93m'}
	if c not in colors:
		print(s)
	else:
		color_start = colors[c]
		print(color_start + s + color_end)

# return a boolean based on yes/no input from user
def get_yes_no(s):
	inp = input("\n" + s + "\t(y/n)\n")
	yes = ["yes", "y", "yeah", "yep", "joo", "kyllä", ""]
	no = ["no", "n", "nope", "nix", "naah", "ei"]
	while inp.lower() not in yes and inp.lower() not in no:
		inp = input("\n" + s + "\t(y/n)\n")
	if inp.lower() in yes:
		res = True
	else:
		res = False
	return res

# writes an iterable to the given file path, one element per row
def write_iterable(it, path="zzz"):
	with open(path, "w") as f:
		for i in it:
			f.write(str(i)+"\n")

# prints an iterable, one element per row
def print_iterable(it):
	for i in it:
		print(i)

