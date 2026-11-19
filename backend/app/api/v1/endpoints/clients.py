import uuid
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate

router = APIRouter()


@router.post(
    "",
    response_model=ClientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Client",
    description="Creates a new client. Automatically associates the client with the authenticated user's workspace.",
)
def create_client(
    client_in: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientRead:
    new_client = Client(
        id=uuid.uuid4(),
        workspace_id=current_user.workspace_id,
        name=client_in.name.strip(),
        contact_email=str(client_in.email).strip().lower() if client_in.email else None,
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return ClientRead.model_validate(new_client)


@router.get(
    "",
    response_model=List[ClientRead],
    summary="List Clients",
    description="Lists all clients within the authenticated user's workspace.",
)
def list_clients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ClientRead]:
    clients = (
        db.query(Client)
        .filter(Client.workspace_id == current_user.workspace_id)
        .order_by(Client.created_at.desc())
        .all()
    )
    return [ClientRead.model_validate(c) for c in clients]


@router.get(
    "/{client_id}",
    response_model=ClientRead,
    summary="Get Client by ID",
    description="Retrieves a specific client by ID within the authenticated user's workspace.",
)
def get_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientRead:
    client = (
        db.query(Client)
        .filter(
            Client.id == client_id,
            Client.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return ClientRead.model_validate(client)


@router.put(
    "/{client_id}",
    response_model=ClientRead,
    summary="Update Client",
    description="Updates a client's details. Enforces strict workspace isolation.",
)
def update_client(
    client_id: UUID,
    client_in: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientRead:
    client = (
        db.query(Client)
        .filter(
            Client.id == client_id,
            Client.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    if client_in.name is not None:
        client.name = client_in.name.strip()
    if client_in.email is not None:
        client.contact_email = str(client_in.email).strip().lower()

    db.commit()
    db.refresh(client)
    return ClientRead.model_validate(client)


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Client",
    description="Deletes a client within the authenticated user's workspace.",
)
def delete_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    client = (
        db.query(Client)
        .filter(
            Client.id == client_id,
            Client.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    db.delete(client)
    db.commit()
    return None
