import pygn


def main():
    clientID = '1984033224-5834A5143CE87D68376F48BF28A6BEE4'
    user_id = pygn.register(clientID)
    print("Here is your Grace Note user ID: {}, \nIt is saved to \'grace_note_user_id.txt\'.".format(user_id))
    f = open('grace_note_user_id.txt', 'w+')
    f.write(user_id)


if __name__ == '__main__':
    main()
