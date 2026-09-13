"""Errores de negocio reutilizados por los routers."""

from fastapi import HTTPException


def resource_not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=404, detail=detail)


def invalid_reference(detail: str) -> HTTPException:
    return HTTPException(status_code=422, detail=detail)


def business_conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=409, detail=detail)
