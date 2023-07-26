
# ! SQLFn example
# ? SELECT: runSQLFn("select", "users", { "where": { "userId": { "condition": "=", "value": interaction.user.id, "type": "AND" } }})
# ? INSERT: runSQLFn("insert", "users", { "insertValue": { "keys": ["userId", "playerId", "bybitApiKey", "bybitApiSecret", "createdDate", "updatedDate"], "columns": [interaction.user.id, "NULL", self.bybitApiKey, self.bybitApiSecret, datetime.today(), datetime.today()] }})
# ? UPDATE: runSQLFn("update", "users", { "where": { "userId": { "condition": "=", "value": interaction.user.id, "type": "AND" }}, "set": { "playerId": select.values[0], "updatedDate": datetime.today() }})
# ? DELETE: runSQLFn("delete", "users", { "where": { "userId": { "condition": "=", "value": interaction.user.id, "type": "AND" }}})

import mysql.connector

mydb = mysql.connector.connect(
    user='root',
    password='',
    host='localhost',
    database='yljr_discord_db'
)

cursor = mydb.cursor(dictionary=True)

class runSQLFn:
    def __init__(self, SQLtype, table, query):
        self.type = SQLtype
        self.table = table
        self.setItems = {};
        self.whereItems = {};
        self.insertItem = {};
        for key in query.keys():
            if key == 'set':
                self.setItems = query['set'].items()
            if key == 'where':
                self.whereItems = query['where'].items()
            if key == 'insertValue':
                self.insertItem = query['insertValue']

    def sqlQuery(self):
        if self.type == "select":
            sql = f"SELECT * FROM `{self.table}`"
        elif self.type == "update":
            sql = f"UPDATE `{self.table}`"
        elif self.type == "insert":
            sql = f"INSERT INTO `{self.table}`"
        elif self.type == "delete":
            sql = f"DELETE FROM `{self.table}`"

        if len(self.insertItem) != 0:
            firstBool = False
            for key in self.insertItem['keys']:
                if firstBool == False:
                    sql += f" (`{key}`"
                    firstBool = True
                else:
                    sql += f", `{key}`"

            sql += ") VALUES"
            
            firstBool = False
            for column in self.insertItem['columns']:
                if firstBool == False:
                    sql += f" ('{column}'"
                    firstBool = True
                else:
                    sql += f", '{column}'"
            
            sql += ")"
        
        if len(self.setItems) != 0:
            firstBool = False
            for key, column in self.setItems:
                if key == 'string':
                    sql += f" {column}"
                elif firstBool == False:
                    sql += f" SET `{key}`='{column}'"
                    firstBool = True
                else:
                    sql += f", `{key}`='{column}'"
            
        if len(self.whereItems) != 0:
            firstBool = False
            for key, column in self.whereItems:
                if key == 'string':
                    sql += f" {column}"
                elif firstBool == False:
                    sql += f" WHERE `{key}`{column['condition']}'{column['value']}'"
                    firstBool = True
                elif column['type'] == 'AND':
                    sql += f" AND `{key}`{column['condition']}'{column['value']}'"
                elif column['type'] == 'OR':
                    sql += f" OR `{key}`{column['condition']}'{column['value']}'"

        cursor.execute(sql)
        row_id = cursor.lastrowid
        if self.type == "select":
            return cursor.fetchall()
        else:
            mydb.commit()
            return row_id