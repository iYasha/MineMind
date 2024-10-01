from pydantic import BaseModel, conlist, constr, Field


class Version(BaseModel):
    name: str
    protocol: int


class PlayerSample(BaseModel):
    id: constr(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    name: str


class Players(BaseModel):
    max: int
    online: int
    sample: PlayerSample = Field(default_factory=list)


class StatusResponse(BaseModel):
    version: Version
    description: dict | str
    players: Players
