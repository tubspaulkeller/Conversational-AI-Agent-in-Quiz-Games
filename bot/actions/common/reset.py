
async def reset_points(sender_id, group_id_opponent, name_of_slot, competition_mode_handler):
    '''
    reset points and evaluated boolean for specific question, just for testing
    '''
    try: 
        filter_competition = {
                    "channel_id": sender_id, 
                    "other_group": group_id_opponent,
                }
        competition_object = await competition_mode_handler.competition_collection .find_one(filter_competition)
        for index, question in enumerate(competition_object['questions']):
            if question['id'] == name_of_slot:
                old_points = competition_object['questions'][index]['points']
                update_points = {
                    "$set": {
                        f"questions.{str(index)}.points": 0,
                        f"questions.{str(index)}.evaluated":False  
                    }
                }
                
                point_filter = {
                    "channel_id": sender_id, 
                    "other_group": group_id_opponent,
                    "questions.id": name_of_slot
                }
                await competition_mode_handler.competition_collection.update_one(point_filter, update_points)
                
                old_total_points = competition_object['total_points']
                # Update totla points
                update_total_points = {
                    "$set": {
                        "total_points": 0
                    }
                }
                await competition_mode_handler.competition_collection .update_one(filter_competition, update_total_points)
                
    except Exception as e:
        print("\033[91mException:\033[0m bei Reset Points %s", e)