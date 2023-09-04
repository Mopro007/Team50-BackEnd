from flask import Flask, request, jsonify
import sqlite3
import re

app = Flask(__name__)

# Signup API route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name, email, password = data.get('name'), data.get('email'), data.get('password')

    # Validate email format using regex
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        response = jsonify({'error': 'Invalid email format'})
        response.status_code = 400  # Bad request
        return response

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,email TEXT,password TEXT,phase INTEGER,project INTEGER)""")

    # Check if email already exists in the database
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        response = jsonify({'error': 'Email already exists'})
        response.status_code = 409  # Conflict
        return response

    # Insert new user into the database
    cursor.execute("INSERT INTO users (name, email, password, phase) VALUES (?, ?, ?, ?)", (name, email, password, 1))
    connection.commit()
    connection.close()
    user = {"name" : name, "email" : email, "password" : password,"phase" : 1, "project": None}
    response = jsonify({'status':'success', 'message': user})
    response.status_code = 200  # Success
    return response

# Signin API route
@app.route('/signin',methods=['POST'])
def signin():
    data = request.get_json()
    email, password = data['email'], data['password']
    users = sqlite3.connect("users.db")
    cursor = users.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(name TEXT,email TEXT,password TEXT, phase INTEGER,project INTEGER)""")
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    users.close()
    if not user:
        response = jsonify({'status':'404', 'message':'Incorrect email or password!'})
    else:
        projects = sqlite3.connect("projects.db")
        cursor = projects.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,description TEXT,participants TEXT)""")
        cursor.execute("SELECT * FROM projects WHERE id=?", (user[5],))
        project = cursor.fetchone()
        projects.close()
        response = jsonify({'status': 'success', 'user': user, 'project': project})
    return response


# Postproject API route
@app.route('/postproject', methods=['POST'])
def postproject():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    participants = data.get('email')

    projects = sqlite3.connect("projects.db")
    cursor = projects.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,description TEXT,participants TEXT)""")
    cursor.execute("INSERT INTO projects (name, description, participants) VALUES (?, ?, ?)", (name, description, participants))
    projects.commit()
    project_id = cursor.lastrowid
    print(project_id)
    projects.close()

    users = sqlite3.connect("users.db")
    cursor = users.cursor()
    cursor.execute("UPDATE users SET project = ?, phase = ? WHERE email = ?", (project_id, 4, participants))
    users.commit()
    users.close()

    response = jsonify({'status':'success','message': 'Project added successfully', 'project_id': project_id, 'name': name, 'description': description, 'participants': participants})
    response.status_code = 200  # Success
    return response


# BrowseProjects API route
@app.route('/browseprojects')
def browseprojects():
    connection = sqlite3.connect("projects.db")
    cursor = connection.cursor()
    cursor.execute("""SELECT id, name, description, participants FROM projects""")
    projects = cursor.fetchall()
    data = []
    for project in projects:
        data.append({"project_id": project[0],"name": project[1], "description": project[2], "participants": project[3].split(', ')})
    connection.close()
    response = jsonify(data)
    return response

# Participate API route
@app.route('/participate', methods=['POST'])
def participate():
    data = request.get_json()
    project_id = data['project_id']
    email = data['email']
    print(project_id)
    print(email)

    connection = sqlite3.connect("projects.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()

    # Add user to the participants of the specified project
    name = project[1]
    description = project[2]
    participants = project[3]
    participants_list = participants.split(', ')
    participants_list.append(email)
    participants_str = ', '.join(participants_list)

    # Update the participants column of the specified project
    cursor.execute("UPDATE projects SET participants = ? WHERE id = ?", (participants_str, project_id))
    connection.commit()
    connection.close()

    users = sqlite3.connect("users.db")
    cursor = users.cursor()
    cursor.execute("UPDATE users SET project = ?, phase = ? WHERE email = ?", (project_id, 4, email))
    users.commit()
    users.close()

    response = jsonify({'status':'success','message': 'Participation added successfully', 'project_id': project_id, 'name': name, 'description': description, 'participants': participants_list})
    print(participants_list)
    response.status_code = 200  # Success
    return response

# UnParticipate API route
@app.route('/unparticipate', methods=['POST'])
def unparticipate():
    data = request.get_json()
    print(data)
    project_id = data.get('project_id')
    email = data.get('email')

    projects = sqlite3.connect("projects.db")
    cursor = projects.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()

    # Get the participants of the specified project
    participants = project[3]
    participants_list = participants.split(', ')

    # Remove user id from participants
    participants_list.remove(email)

    # Convert participants list back to a string
    participants_str = ', '.join(participants_list)

    # Update the participants column of the specified project
    cursor.execute("UPDATE projects SET participants = ? WHERE id = ?", (participants_str, project_id))
    projects.commit()
    projects.close()

    users = sqlite3.connect("users.db")
    cursor = users.cursor()
    cursor.execute("UPDATE users SET project = ?, phase = ? WHERE email = ?", (None, 1, email))
    users.commit()
    users.close()

    response = jsonify({'status':'success','message': 'Participation removed successfully'})
    response.status_code = 200  # Success
    return response

if __name__ == "__main__":
    app.run(debug=True)
