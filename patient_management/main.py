
from fastapi import FastAPI

from middleware.auth_middleware import AuthMiddleware

from routers.auth import router as auth_router
from routers.test_auth import router as test_auth_router
from routers.patients import router as patients_router
from routers.providers import router as providers_router
from routers.appointments import router as appointments_router
from routers.prescriptions import router as prescriptions_router
from routers.provider_availability import router as provider_availability_router
from routers.provider_time_off import router as provider_time_off_router
from routers.allergies import router as allergies_router
from routers.patient_allergies import router as patient_allergies_router
from routers.specialties import router as specialties_router
from routers.provider_specialties import router as provider_specialties_router
from routers import visit_notes
from middleware.rate_limit import RateLimitMiddleware
from routers.internal_documents import router as internal_documents_router
from routers.internal_appointments import router as internal_appointments_router
from routers.assistant import router as assistant_router
app = FastAPI(
    title="Patient Care Assistant API",
    description="Healthcare Management API",
    version="1.0.0"
)


# Middleware

app.add_middleware(
    AuthMiddleware
)

app.add_middleware(
    RateLimitMiddleware
)


# Routers

app.include_router(auth_router)

app.include_router(test_auth_router)
app.include_router(patients_router)
app.include_router(providers_router)
app.include_router(appointments_router)
app.include_router(prescriptions_router)
app.include_router(provider_availability_router)
app.include_router(provider_time_off_router)
app.include_router(internal_documents_router)
app.include_router(allergies_router)
app.include_router(patient_allergies_router)
app.include_router(specialties_router)
app.include_router(provider_specialties_router)
app.include_router(visit_notes.router)
app.include_router(internal_appointments_router)
app.include_router(assistant_router)
@app.get("/")
def root():

    return {
        "message": "Patient Care Assistant API is running"
    }
