import user
from user import User
import copy
from termcolor import colored, cprint

def iter_da_within_group(people, people_ids, people_min, people_max, matches, all_users_ids):
    # precompute whether each user is within this group of people
    group_dict = {}
    for u_id in all_users_ids:
        group_dict[u_id] = False
    for u_id in people_ids:
        group_dict[u_id] = True

    # form initial preference lists
    for u in people:
        u.temp_prefs = []
        for user_id in u.prefs:
            if group_dict[user_id] == True:
                u.temp_prefs.append(user_id)
        u.temp_prefs.append(0) # represents not getting matched

    # duplicate the users
    propose = copy.deepcopy(people)
    receive = copy.deepcopy(people)
    propose_dict = user.map_users_list_to_dict(propose)
    receive_dict = user.map_users_list_to_dict(receive)

    # dictionary for how many matches have been obtained: shared between propose and receive
    matches_obtained = {}
    for u_id in people_ids:
        matches_obtained[u_id] = 0

    #dictionary for whether dropped out: shared between propose and receive
    dropped_out = {}
    for u_id in people_ids:
        dropped_out[u_id] = False

    need_more_matches = True
    num_iters = 0
    while (need_more_matches):
        print "\rRunning iteration %d" % num_iters,

        still_unmatched_proposers = True

        while (still_unmatched_proposers):
            # do proposing
            for u in propose:
                if dropped_out[u.id]:
                    continue

                if u.current_match is None:
                    target_id = None
                    while True:
                        target_id = u.temp_prefs[u.prop_pos]
                        if target_id == 0:
                        # not getting matched this round
                            u.current_match = 0
                            break
                        u.prop_pos += 1

                        if (not dropped_out[target_id]):
                            # found a valid target id
                            break

                    if target_id != 0:
                        target = receive_dict[target_id]

                        if (target.current_match is None) or (target.temp_prefs.index(u.id) < target.rec_rank):
                            # accept the proposal
                            if target.current_match is not None:
                                propose_dict[target.current_match].current_match = None
                            u.current_match = target.id
                            target.current_match = u.id
                            target.rec_rank = target.temp_prefs.index(u.id)

            # check if any proposers are still unmatched
            still_unmatched_proposers = False
            for u in propose:
                if dropped_out[u.id]:
                    continue

                if u.current_match is None:
                    still_unmatched_proposers = True
                    break

        # add matches from this round to master matches list
        # remove this round's match from preference list
        # reset user fields for next iteration
        for u in propose:
            if dropped_out[u.id]:
                continue
            if u.current_match != 0:
                if (u.current_match not in matches[u.id]):
                    matches[u.id].append(u.current_match)
                    matches_obtained[u.id] += 1
                if u.current_match is not None:
                    u.temp_prefs.remove(u.current_match)
            u.prop_pos = 0
            u.current_match = None
        for u in receive:
            if dropped_out[u.id]:
                continue
            if (u.current_match is not None):
                if (u.current_match not in matches[u.id]):
                    matches[u.id].append(u.current_match)
                    matches_obtained[u.id] += 1
                u.temp_prefs.remove(u.current_match)
            u.rec_rank = None
            u.current_match = None

        # check if any user still needs more matches
        # flag any users that are dropping out
        need_more_matches = False
        for u in propose:
            if matches_obtained[u.id] < people_min:
                need_more_matches = True
            elif matches_obtained[u.id] >= people_max:
                dropped_out[u.id] = True

        num_iters += 1

        sat_prop = [u for u in propose if matches_obtained[u.id] < people_min]
        sat_rec = [u for u in receive if matches_obtained[u.id] < people_min]
        drop_prop = [u for u in propose if not dropped_out[u.id]]
        drop_rec = [u for u in receive if not dropped_out[u.id]]
        print "(%d propose not done, %d receive not done)" % (len(sat_prop), len(sat_rec)),
        print "(%d propose avail. left, %d receive avail. left)" % (len(drop_prop), len(drop_rec)),

        if num_iters > 100:
            print colored("Failed to meet min matches", 'red', attrs=['bold'])
            return matches

    print colored("Finished matching stage!", 'green', attrs=['bold'])

    return matches


def iter_da_between_groups(proposer, propose_ids, receiver, receive_ids, prop_min, rec_min, prop_max, rec_max, matches, all_users_ids):
    propose = copy.deepcopy(proposer)
    receive = copy.deepcopy(receiver)
    propose_dict = user.map_users_list_to_dict(propose)
    receive_dict = user.map_users_list_to_dict(receive)

    prop_dict = {}
    for u_id in all_users_ids:
        prop_dict[u_id] = False
    for u_id in propose_ids:
        prop_dict[u_id] = True
    rec_dict = {}
    for u_id in all_users_ids:
        rec_dict[u_id] = False
    for u_id in receive_ids:
        rec_dict[u_id] = True

    # form initial preference lists
    for u in propose:
        u.temp_prefs = []
        for user_id in u.prefs:
            if rec_dict[user_id] == True:
                u.temp_prefs.append(user_id)
        u.temp_prefs.append(0) # represents not getting matched
    for u in receive:
        u.temp_prefs = []
        for user_id in u.prefs:
            if prop_dict[user_id] == True:
                u.temp_prefs.append(user_id)
        u.temp_prefs.append(0) # represents not getting matched

    # assign number of matches so far
    for u in propose:
        u.matches_obtained = 0
    for u in receive:
        u.matches_obtained = 0

    need_more_matches = True
    num_iters = 1
    while need_more_matches:
        print "\rRunning iteration %d" % num_iters,
        # start new iteration of DA
        still_unmatched_proposers = True
        while (still_unmatched_proposers):
            # do proposing
            for u in propose:
                if u.dropped_out:
                    continue

                if u.current_match is None:
                    target_id = None
                    while True:
                        target_id = u.temp_prefs[u.prop_pos]
                        if target_id == 0:
                        # not getting matched this round
                            u.current_match = 0
                            break
                        u.prop_pos += 1

                        if (not receive_dict[target_id].dropped_out):
                            # found a valid target id
                            break

                    if target_id != 0:
                        target = receive_dict[target_id]
                        if (target.current_match is None) or (target.temp_prefs.index(u.id) < target.rec_rank):
                            # accept the proposal
                            if target.current_match is not None:
                                propose_dict[target.current_match].current_match = None
                            u.current_match = target.id
                            target.current_match = u.id
                            target.rec_rank = target.temp_prefs.index(u.id)

            # check if any proposers are still unmatched
            unmatched_props = [u for u in propose if (not u.dropped_out and u.current_match is None)]
            still_unmatched_proposers = False
            for u in propose:
                if u.dropped_out:
                    continue
                if u.current_match is None:
                    still_unmatched_proposers = True
                    break
            print "\rRunning iteration %d (Number unmatched in DA sub-round: %d)" % (num_iters, len(unmatched_props)),

        # add matches from this round to master matches list
        # remove this round's match from preference list
        # reset user fields for next iteration
        # update matches_needed for bigger side
        for u in propose:
            if u.dropped_out:
                continue
            if u.current_match != 0:
                if (u.current_match not in matches[u.id]):
                    matches[u.id].append(u.current_match)
                    u.matches_obtained += 1
                if u.current_match is not None:
                    u.temp_prefs.remove(u.current_match)
            u.prop_pos = 0
            u.current_match = None
        for u in receive:
            if u.dropped_out:
                continue
            if (u.current_match is not None):
                if (u.current_match not in matches[u.id]):
                    matches[u.id].append(u.current_match)
                    u.matches_obtained += 1
                u.temp_prefs.remove(u.current_match)
            u.rec_rank = None
            u.current_match = None

        # check if any user still needs more matches
        # flag any users that are dropping out
        need_more_matches = False
        for u in propose:
            if u.matches_obtained < prop_min:
                need_more_matches = True
                #print "prop" + str(u.matches_obtained)
            elif u.matches_obtained >= prop_max:
                u.dropped_out = True
        for u in receive:
            if u.matches_obtained < rec_min:
                need_more_matches = True
                #print "rec" + str(u.matches_obtained)
            elif u.matches_obtained >= rec_max:
                u.dropped_out = True

        sat_prop = [u for u in propose if u.matches_obtained < prop_min]
        sat_rec = [u for u in receive if u.matches_obtained < rec_min]
        drop_prop = [u for u in propose if not u.dropped_out]
        drop_rec = [u for u in receive if not u.dropped_out]
        print "\rRunning iteration %d (%d propose not done, %d receive not done)" % (num_iters, len(sat_prop), len(sat_rec)),
        print "(%d propose avail. left, %d receive avail. left)" % (len(drop_prop), len(drop_rec)),

        num_iters += 1
        if num_iters > 100:
            print colored("Failed to meet min matches", 'red', attrs=['bold'])
            return matches

    print colored("Finished matching stage!", 'green', attrs=['bold'])
    return matches

# return matches on all users
def run_iter_da_for_all():

    # random users...
    # users = user.gen_users(500)
    # users = user.calc_prefs(users, save=False)
    # users = user.filter_prefs(users)

    # saved random users...
    users = user.load_users('random_data_1500.txt')
    users = user.load_features(users, 'random_features_1500.txt')
    users = user.load_prefs(users, 'random_prefs_1500.txt')
    users = user.filter_prefs(users)

    # or actual users...?
    # users = user.load_users('anon_data_2016.txt')
    # users = user.load_features(users, 'features_2016.txt')
    # users = user.load_prefs(users, 'preferences_2016.txt')
    # users = user.filter_prefs(users)

    users_dict = user.map_users_list_to_dict(users)
    all_users_ids = users_dict.keys()

    ########    PARAMETERS    ###############################
    mixing_ratio = 0.6 # proportion of the matches that come from the different stages

    overall_female_min = 8 # overall_female_min * mixing_ratio & overall_female_min * (1-mixing_ratio) are lower bounds on # matches for females in between groups algo
    overall_male_min = 1 # overall_male_min * mixing_ratio & overall_male_min * (1-mixing_ratio) are lower bounds on # matches for males in between groups algo
    overall_within_group_min = 9 # overall_within_group_min * mixing_ratio & overall_within_group_min * (1-mixing_ratio) are lower bounds on # matches for within group algo
    # (These approximately translate to lower bounds on # matches overall)

    dropout_female_factor = 1.2 # scalar multiple to set diff. btwn. female min & max # of matches in between groups algo
    dropout_male_factor = 18.0 # scalar multiple to set diff. btwn. male min & max # of matches in between groups algo
    dropout_within_group_factor = 1.3 # scalar multiple to set diff. btwn. min & max # of matches in within groups algo
    # (max # of matches <=> user dropping out in the algo)

    '''
    GROUPING
    Sort users into preference groups
    Record ids for each group
    Set up dictionary to hold everyone's matchings
    '''

    matches = {}
    homo_male = []
    homo_female = []
    heter_male = []
    heter_female = []
    bi_male = []
    bi_female = []
    homo_m_id = []
    homo_f_id = []
    heter_m_id = []
    heter_f_id = []
    bi_m_id = []
    bi_f_id = []
    for u in users:
        matches[u.id] = []
        if u.gender == 0:
            if u.seeking == 0:
                homo_male.append(u)
                homo_m_id.append(u.id)
            elif u.seeking == 1:
                heter_male.append(u)
                heter_m_id.append(u.id)
            else:
                bi_male.append(u)
                bi_m_id.append(u.id)
        else:
            if u.seeking == 0:
                heter_female.append(u)
                heter_f_id.append(u.id)
            elif u.seeking == 1:
                homo_female.append(u)
                homo_f_id.append(u.id)
            else:
                bi_female.append(u)
                bi_f_id.append(u.id)


    #print len(homo_m_id)
    #print len(bi_m_id)
    #print len(homo_f_id)
    #print len(bi_f_id)
    #print len(heter_m_id)
    #print len(heter_f_id)

    # temporarily truncate for test reasons
    #heter_male = heter_male[:163]
    #heter_female = heter_female[:199]
    #heter_m_id = heter_m_id[:163]
    #heter_f_id = heter_f_id[:199]

    '''
    ITERATED DA
    Find matches in 6 stages
    '''
    print colored("Computing matchings for homosexual & bisexual males...", 'magenta', attrs=['bold'])
    min_target = (overall_within_group_min * mixing_ratio)
    matches = iter_da_within_group((homo_male + bi_male), (homo_m_id + bi_m_id), min_target, min_target*dropout_within_group_factor, matches, all_users_ids)
    print colored("Computing matchings for homosexual & bisexual females...", 'magenta', attrs=['bold'])
    min_target = (overall_within_group_min * mixing_ratio)
    matches = iter_da_within_group((homo_female + bi_female), (homo_f_id + bi_f_id), min_target, min_target*dropout_within_group_factor, matches, all_users_ids)
    print colored("Computing matchings for homosexual males...", 'magenta', attrs=['bold'])
    min_target = (overall_within_group_min * (1.0 - mixing_ratio))
    matches = iter_da_within_group(homo_male, homo_m_id, min_target, min_target*dropout_within_group_factor, matches, all_users_ids)
    print colored("Computing matchings for homosexual females...", 'magenta', attrs=['bold'])
    min_target = (overall_within_group_min * (1.0 - mixing_ratio))
    matches = iter_da_within_group(homo_female, homo_f_id, min_target, min_target*dropout_within_group_factor, matches, all_users_ids)
    print colored("Computing matchings for bisexual & heterosexual males & females...", 'magenta', attrs=['bold'])
    min_target_female = (overall_female_min * (1.0 - mixing_ratio))
    min_target_male = (overall_male_min * (1.0 - mixing_ratio))
    #matches = iter_da_between_groups((heter_male + bi_male), (heter_m_id + bi_m_id), (heter_female + bi_female), (heter_f_id + bi_f_id), min_target_male, min_target_female, min_target_male * dropout_male_factor, min_target_female * dropout_female_factor, matches, all_users_ids)
    matches = iter_da_between_groups((heter_female + bi_female), (heter_f_id + bi_f_id), (heter_male + bi_male), (heter_m_id + bi_m_id), min_target_female, min_target_male, min_target_female * dropout_female_factor, min_target_male * dropout_male_factor, matches, all_users_ids)
    print colored("Computing matchings for heterosexual males & females...", 'magenta', attrs=['bold'])
    min_target_female = (overall_female_min * (mixing_ratio))
    min_target_male = (overall_male_min * (mixing_ratio))
    #matches = iter_da_between_groups(heter_male, heter_m_id, heter_female, heter_f_id, min_target_male, min_target_female, min_target_male * dropout_male_factor, min_target_female * dropout_female_factor, matches, all_users_ids)
    matches = iter_da_between_groups(heter_female, heter_f_id, heter_male, heter_m_id, min_target_female, min_target_male, min_target_female * dropout_female_factor, min_target_male * dropout_male_factor, matches, all_users_ids)

    # create ranked list for each person by sorting their matches
    user.sort_all_match_lists(matches, users_dict)

    print colored("Matching completed!", 'red', 'on_green', attrs=['bold'])

    # check on how many matches people actually have
    user.analyze_num_matches(matches, users_dict)

    for i in range(1, 4, 1):
        print '\033[95m#####################################'
        print 'TOP %s MATCHES' % i
        print '#####################################\033[0m'
        #check the utility values from rank perspective and distance perspective -- in two separate functions
        user.analyze_rank_utility(matches, users_dict, i)
        user.analyze_distance_utility(matches, users_dict, i)

run_iter_da_for_all()
