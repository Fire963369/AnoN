from flask import Flask, request, redirect, render_template_string, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import html
import click
import os

# --- Application Setup ---
app = Flask(__name__)

# --- Configuration ---
# Use DATABASE_URL from environment variables (provided by Render)
# Fallback to local sqlite for development (optional)
# Replace postgres:// with postgresql:// for SQLAlchemy compatibility
db_url = os.environ.get('DATABASE_URL', 'sqlite:///forum.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Use SECRET_KEY from environment variables (set this in Render)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-secret-key-CHANGE-ME') # Provide a default for local dev if needed

# --- Database and Login Manager Initialization ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Route name for the login page

# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    replies = db.relationship('Reply', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    replies = db.relationship('Reply', backref='post', lazy=True, cascade='all, delete-orphan')

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- Base HTML Template ---
def base_html(title, content):
    user_section = ''
    if current_user.is_authenticated:
        user_section = f'''
            <div class="flex items-center space-x-4">
                <span class="text-gray-700 dark:text-gray-300">Привет, {html.escape(current_user.username)}!</span>
                <a href="{url_for('logout')}" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">Выйти</a>
            </div>
        '''
    else:
        user_section = f'''
            <div class="flex items-center space-x-4">
                <a href="{url_for('login')}" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">Войти</a>
                <a href="{url_for('register')}" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">Зарегистрироваться</a>
            </div>
        '''

    # (Keep the rest of the base_html function as it was)
    return f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{html.escape(title)} - Форум</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
          tailwind.config = {{
            darkMode: 'media',
            theme: {{
              extend: {{
                colors: {{
                  background: 'hsl(var(--background))',
                  foreground: 'hsl(var(--foreground))',
                  card: 'hsl(var(--card))',
                  'card-foreground': 'hsl(var(--card-foreground))',
                  popover: 'hsl(var(--popover))',
                  'popover-foreground': 'hsl(var(--popover-foreground))',
                  primary: 'hsl(var(--primary))',
                  'primary-foreground': 'hsl(var(--primary-foreground))',
                  secondary: 'hsl(var(--secondary))',
                  'secondary-foreground': 'hsl(var(--secondary-foreground))',
                  muted: 'hsl(var(--muted))',
                  'muted-foreground': 'hsl(var(--muted-foreground))',
                  accent: 'hsl(var(--accent))',
                  'accent-foreground': 'hsl(var(--accent-foreground))',
                  destructive: 'hsl(var(--destructive))',
                  'destructive-foreground': 'hsl(var(--destructive-foreground))',
                  border: 'hsl(var(--border))',
                  input: 'hsl(var(--input))',
                  ring: 'hsl(var(--ring))',
                }},
                borderRadius: {{
                  lg: 'var(--radius)',
                  md: 'calc(var(--radius) - 5px)',
                  sm: 'calc(var(--radius) - 10px)',
                }},
              }}
            }}
          }}
        </script>
        <style type="text/tailwindcss">
            @layer base {{
              :root {{
                --background: 0 0% 100%;
                --foreground: 222.2 84% 4.9%;
                --card: 0 0% 100%;
                --card-foreground: 222.2 84% 4.9%;
                --popover: 0 0% 100%;
                --popover-foreground: 222.2 84% 4.9%;
                --primary: 222.2 47.4% 11.2%;
                --primary-foreground: 210 40% 98%;
                --secondary: 210 40% 96.1%;
                --secondary-foreground: 222.2 47.4% 11.2%;
                --muted: 210 40% 96.1%;
                --muted-foreground: 215.4 16.3% 46.9%;
                --accent: 210 40% 96.1%;
                --accent-foreground: 222.2 47.4% 11.2%;
                --destructive: 0 84.2% 60.2%;
                --destructive-foreground: 210 40% 98%;
                --border: 214.3 31.8% 91.4%;
                --input: 214.3 31.8% 91.4%;
                --ring: 222.2 84% 4.9%;
                --radius: 2rem;
              }}

              .dark {{
                --background: 222.2 84% 4.9%;
                --foreground: 210 40% 98%;
                --card: 222.2 84% 4.9%;
                --card-foreground: 210 40% 98%;
                --popover: 222.2 84% 4.9%;
                --popover-foreground: 210 40% 98%;
                --primary: 210 40% 98%;
                --primary-foreground: 222.2 47.4% 11.2%;
                --secondary: 217.2 32.6% 17.5%;
                --secondary-foreground: 210 40% 98%;
                --muted: 217.2 32.6% 17.5%;
                --muted-foreground: 215 20.2% 65.1%;
                --accent: 217.2 32.6% 17.5%;
                --accent-foreground: 210 40% 98%;
                --destructive: 0 62.8% 30.6%;
                --destructive-foreground: 210 40% 98%;
                --border: 217.2 32.6% 17.5%;
                --input: 217.2 32.6% 17.5%;
                --ring: 212.7 26.8% 83.9%;
              }}
            }}

            @layer base {{
              * {{
                @apply border-border;
              }}
              body {{
                @apply bg-background text-foreground;
                font-family: 'Inter', sans-serif; /* Example font */
              }}
            }}
        </style>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
    </head>
    <body class="bg-background text-foreground min-h-screen antialiased">
        <div class="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
            <header class="flex justify-between items-center mb-8 pb-4 border-b border-border">
                 <a href="{url_for('index')}" class="text-2xl font-bold text-primary dark:text-primary-foreground">Форум</a>
                {user_section}
            </header>
            <main>
                {content}
            </main>
            <footer class="mt-12 pt-4 text-center text-sm text-muted-foreground border-t border-border">
                AnonN (от учеников техноlyceum) &copy; {datetime.utcnow().year}
            </footer>
        </div>
    </body>
    </html>
    '''


# --- Routes ---
@app.route('/')
def index():
    posts = Post.query.order_by(Post.date.desc()).all()
    posts_html_list = []

    for post in posts:
        # Generate HTML for replies to this post
        replies_html = ''.join([
            f'''<div class="ml-6 sm:ml-10 mt-4 p-4 bg-secondary dark:bg-secondary rounded-md border border-border">
                   <div class="text-xs text-muted-foreground mb-2">
                       @{html.escape(reply.author.username)} - {reply.date.strftime("%d.%m.%Y %H:%M")}
                   </div>
                   <div class="text-sm text-secondary-foreground dark:text-secondary-foreground whitespace-pre-wrap">{html.escape(reply.content)}</div>
               </div>'''
            for reply in post.replies
        ])

        # **FIX:** Generate delete link HTML conditionally beforehand
        delete_link_html = ''
        if current_user.is_authenticated and (current_user.is_admin or current_user.id == post.user_id):
             # Use single quotes inside confirm() to avoid escaping issues with onclick's double quotes
            delete_link_html = f'''<a href="{url_for("delete_post", post_id=post.id)}"
                                    onclick="return confirm('Вы уверены, что хотите удалить этот пост?');"
                                    class="text-red-500 hover:text-red-700 ml-4 text-xs">
                                    [Удалить пост]
                                 </a>'''

        # Generate HTML for the post itself, including reply form and replies
        # Форма ответа (только для авторизованных)
        reply_form = ''
        if current_user.is_authenticated:
            reply_form = f'''
            <form method="POST" action="{url_for('reply', post_id=post.id)}" class="mt-4">
                <textarea name="content" required placeholder="Ваш ответ..."
                        class="w-full p-2 border border-input rounded-md h-24 bg-background dark:bg-input text-foreground dark:text-foreground focus:ring-2 focus:ring-ring focus:border-transparent outline-none resize-none text-sm"></textarea>
                <button type="submit"
                        class="mt-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring dark:bg-primary dark:text-primary-foreground dark:hover:bg-primary/90">
                    Ответить
                </button>
            </form>
            '''
        else:
            reply_form = '<p class="mt-4 text-sm text-muted-foreground"><a href="/login" class="text-blue-600 dark:text-blue-400 hover:underline">Войдите</a>, чтобы ответить.</p>'

    # Combine all post HTML strings
    all_posts_html = ''.join(posts_html_list) if posts_html_list else '<p class="text-center text-muted-foreground">Пока нет сообщений.</p>'

    # New Post Form (only if logged in)
    new_post_form = ''
    if current_user.is_authenticated:
        new_post_form = f'''
        <form method="POST" action="{url_for('create_post')}" class="mb-8 p-5 bg-card dark:bg-card rounded-lg border border-border shadow-sm">
            <h2 class="text-lg font-semibold text-card-foreground dark:text-card-foreground mb-3">Новое сообщение</h2>
            <textarea name="content" required placeholder="Напишите что-нибудь..."
                      class="w-full p-2 border border-input rounded-md h-28 bg-background dark:bg-input text-foreground dark:text-foreground focus:ring-2 focus:ring-ring focus:border-transparent outline-none resize-none text-sm"></textarea>
            <button type="submit"
                    class="mt-3 px-5 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring dark:bg-primary dark:text-primary-foreground dark:hover:bg-primary/90">
                Опубликовать
            </button>
        </form>
        '''
    else:
         new_post_form = '<p class="mb-8 text-center text-muted-foreground"><a href="/login" class="text-blue-600 dark:text-blue-400 hover:underline">Войдите</a>, чтобы опубликовать сообщение.</p>'


    # Render the full page
    page_content = f'''
        {new_post_form}
        <h2 class="text-xl font-semibold text-foreground dark:text-foreground mb-4">Лента сообщений AnonN:</h2>
        {all_posts_html}
    '''
    return render_template_string(base_html('Главная', page_content))


@app.route('/post', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content') # Use .get for safety
    if content: # Basic validation
        post = Post(content=content, author=current_user)
        db.session.add(post)
        db.session.commit()
    # Add flash messaging later for better feedback
    return redirect(url_for('index'))


@app.route('/reply/<int:post_id>', methods=['POST'])
@login_required
def reply(post_id):
    post = db.session.get(Post, post_id) # Check if post exists
    content = request.form.get('content')
    if post and content:
        reply_obj = Reply(content=content, post_id=post_id, author=current_user)
        db.session.add(reply_obj)
        db.session.commit()
    # Add flash messaging later
    return redirect(url_for('index'))


@app.route('/delete_post/<int:post_id>', methods=['GET']) # Changed to GET for link, added confirmation
@login_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)
    if post and (current_user.is_admin or post.user_id == current_user.id):
        # cascade='all, delete-orphan' in Post model handles deleting replies
        db.session.delete(post)
        db.session.commit()
        # Add flash message: "Post deleted"
    else:
        # Add flash message: "Permission denied" or "Post not found"
        pass
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # Redirect if already logged in

    error_message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next') # For redirecting after login
            return redirect(next_page or url_for('index'))
        else:
            error_message = '<div class="mb-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">Неверный логин или пароль.</div>'
            # Consider adding flash messages instead

    # Login form using Tailwind classes
    login_form_html = f'''
        <div class="max-w-md mx-auto mt-10 p-6 bg-card dark:bg-card rounded-lg border border-border shadow-md">
            <h2 class="text-2xl font-semibold text-center text-card-foreground dark:text-card-foreground mb-6">Вход</h2>
            {error_message}
            <form method="POST" class="space-y-4">
                <div>
                    <label for="username" class="block text-sm font-medium text-muted-foreground mb-1">Логин</label>
                    <input type="text" id="username" name="username" required
                           class="w-full px-3 py-2 border border-input rounded-md bg-background dark:bg-input text-foreground dark:text-foreground focus:ring-2 focus:ring-ring focus:border-transparent outline-none text-sm"
                           placeholder="Ваш логин">
                </div>
                <div>
                    <label for="password" class="block text-sm font-medium text-muted-foreground mb-1">Пароль</label>
                    <input type="password" id="password" name="password" required
                           class="w-full px-3 py-2 border border-input rounded-md bg-background dark:bg-input text-foreground dark:text-foreground focus:ring-2 focus:ring-ring focus:border-transparent outline-none text-sm"
                           placeholder="Ваш пароль">
                </div>
                <button type="submit"
                        class="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring dark:bg-primary dark:text-primary-foreground dark:hover:bg-primary/90">
                    Войти
                </button>
            </form>
            <p class="mt-6 text-center text-sm text-muted-foreground">
                Нет аккаунта? <a href="{url_for('register')}" class="text-blue-600 dark:text-blue-400 hover:underline">Зарегистрироваться</a>
            </p>
        </div>
    '''
    return render_template_string(base_html('Вход', login_form_html))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # Redirect if already logged in

    error_message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Basic validation (add more robust validation as needed)
        if not username or not password:
             error_message = '<div class="mb-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">Логин и пароль обязательны.</div>'
        elif User.query.filter_by(username=username).first():
            error_message = '<div class="mb-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">Пользователь с таким именем уже существует.</div>'
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password_hash=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            # Add flash message: "Registration successful, please log in."
            return redirect(url_for('login')) # Redirect to login after successful registration

    # Registration form using Tailwind classes
    register_form_html = f'''
        <div class="max-w-md mx-auto mt-10 p-6 bg-card dark:bg-card rounded-lg border border-border shadow-md">
            <h2 class="text-2xl font-semibold text-center text-card-foreground dark:text-card-foreground mb-6">Регистрация</h2>
            {error_message}
            <form method="POST" class="space-y-4">
                <div>
                    <label for="username" class="block text-sm font-medium text-muted-foreground mb-1">Логин</label>
                    <input type="text" id="username" name="username" required
                           class="w-full px-3 py-2 border border-input rounded-md bg-background dark:bg-input text-foreground dark:text-foreground focus:ring-2 focus:ring-ring focus:border-transparent outline-none text-sm"
                           placeholder="Придумайте логин">
                </div>
                <div>
                    <label for="password" class="block text-sm font-medium text-muted-foreground mb-1">Пароль</label>
                    <input type="password" id="password" name="password" required
                           class="w-full px-3 py-2 border border-input rounded-md bg-background dark:bg-input text-foreground dark:text-foreground focus:ring-2 focus:ring-ring focus:border-transparent outline-none text-sm"
                           placeholder="Придумайте пароль">
                </div>
                <button type="submit"
                        class="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring dark:bg-primary dark:text-primary-foreground dark:hover:bg-primary/90">
                    Зарегистрироваться
                </button>
            </form>
             <p class="mt-6 text-center text-sm text-muted-foreground">
                Уже есть аккаунт? <a href="{url_for('login')}" class="text-blue-600 dark:text-blue-400 hover:underline">Войти</a>
            </p>
        </div>
    '''
    return render_template_string(base_html('Регистрация', register_form_html))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    # Add flash message: "You have been logged out."
    return redirect(url_for('index'))


# --- CLI Commands ---
# These commands can be run via Render's shell or potentially as part of a build script
@app.cli.command("init-db")
def init_db():
    """Creates the database tables based on models."""
    # Wrap in app_context to ensure database connection is available
    with app.app_context():
        db.create_all()
    print("Database tables created (if they didn't exist).")

@app.cli.command("create-admin")
@click.argument("username")
@click.argument("password")
def create_admin(username, password):
    """Creates an admin user."""
    with app.app_context(): # Ensure app context for database operations
        if User.query.filter_by(username=username).first():
            print(f"Error: User '{username}' already exists.")
            return

        hashed_pw = generate_password_hash(password)
        admin = User(username=username, password_hash=hashed_pw, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user '{username}' created successfully.")

# --- Removed the __main__ block ---
# The application will be run by Gunicorn specified in the Procfile
# Example: gunicorn app:app
