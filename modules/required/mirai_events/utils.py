from graia.ariadne.model.relationship import Member, Group

from shared.utils.time import timestamp_format


def unpack_member(member: Member | None) -> dict:
    """ use: **unpack_member(member) """
    return {
        "member_id": member.id if member else "",
        "member_name": member.name if member else "",
        "member_permission": member.permission if member else "",
        "member_special_title": member.special_title if member else "",
        "member_join_timestamp": timestamp_format(member.join_timestamp) if member else "",
        "member_last_speak_timestamp": timestamp_format(member.last_speak_timestamp) if member else "",
        "member_mute_time": timestamp_format(member.mute_time) if member else ""
    }


def unpack_group(group: Group | None) -> dict:
    """ use: **unpack_group(group) """
    return {
        "group_id": group.id if group else "",
        "group_name": group.name if group else ""
    }


def unpack_operator(operator: Member | None) -> dict:
    """ use: **unpack_operator(operator) """
    return {
        "operator_id": operator.id if operator else "",
        "operator_name": operator.name if operator else "",
        "operator_permission": operator.permission if operator else "",
        "operator_special_title": operator.special_title if operator else "",
        "operator_join_timestamp": timestamp_format(operator.join_timestamp) if operator else "",
        "operator_last_speak_timestamp": timestamp_format(operator.last_speak_timestamp) if operator else "",
        "operator_mute_time": timestamp_format(operator.mute_time) if operator else ""
    }


def unpack_invitor(invitor: Member | None) -> dict:
    """ use: **unpack_operator(operator) """
    return {
        "invitor_id": invitor.id if invitor else "",
        "invitor_name": invitor.name if invitor else "",
        "invitor_permission": invitor.permission if invitor else "",
        "invitor_special_title": invitor.special_title if invitor else "",
        "invitor_join_timestamp": timestamp_format(invitor.join_timestamp) if invitor else "",
        "invitor_last_speak_timestamp": timestamp_format(invitor.last_speak_timestamp) if invitor else "",
        "invitor_mute_time": timestamp_format(invitor.mute_time) if invitor else ""
    }
