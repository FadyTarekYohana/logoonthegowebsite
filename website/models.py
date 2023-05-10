from dataclasses import dataclass
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


@dataclass
class User:
    username: str
    id: str
    email: str

    @staticmethod
    def from_dict(obj: Any) -> 'User':
        assert isinstance(obj, dict)
        username = from_str(obj.get("username"))
        id = from_str(obj.get("id"))
        email = from_str(obj.get("email"))
        return User(username, id, email)

    def to_dict(self) -> dict:
        result: dict = {}
        result["username"] = from_str(self.username)
        result["id"] = from_str(self.id)
        result["email"] = from_str(self.email)
        return result


def user_from_dict(s: Any) -> User:
    return User.from_dict(s)


def user_to_dict(x: User) -> Any:
    return to_class(User, x)
