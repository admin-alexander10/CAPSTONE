import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.subscription import InstitutionAccount, InstitutionInvite, InstitutionMember, PlanCatalog, UserSubscription
from app.models.user import Usuario
from app.schemas.subscription import (
    CheckoutSessionResponse,
    CreateCheckoutRequest,
    InstitutionMemberResponse,
    InstitutionPricingResponse,
    PlanItem,
    SubscriptionStatusResponse,
)

try:
    import stripe
except ImportError:  # pragma: no cover
    stripe = None


class SubscriptionService:
    """Módulo de suscripciones y planes comerciales realista para producción."""

    def __init__(self, db: Session):
        self.db = db

    def ensure_default_plans(self) -> List[PlanCatalog]:
        defaults = [
            {
                "code": "free",
                "name": "Free",
                "price": 0.0,
                "currency": "PEN",
                "interval": "monthly",
                "tier": "free",
                "included_users": 1,
                "extra_seat_price": 0.0,
                "features": ["1 usuario", "SOS básico", "Red familiar"],
                "stripe_price_id": None,
            },
            {
                "code": "pro",
                "name": "Pro",
                "price": 89.0,
                "currency": "PEN",
                "interval": "monthly",
                "tier": "pro",
                "included_users": 5,
                "extra_seat_price": 25.0,
                "features": ["Alertas avanzadas", "Mapa geolocalizado", "Captura antirrobo"],
                "stripe_price_id": settings.STRIPE_PRICE_ID_PRO,
            },
            {
                "code": "enterprise",
                "name": "Enterprise",
                "price": 299.0,
                "currency": "PEN",
                "interval": "custom",
                "tier": "enterprise",
                "included_users": 10,
                "extra_seat_price": 35.0,
                "features": ["Multi-sede", "Integración B2G", "Múltiples usuarios institucionales"],
                "stripe_price_id": settings.STRIPE_PRICE_ID_ENTERPRISE,
            },
        ]

        created: List[PlanCatalog] = []
        for plan in defaults:
            existing = self.db.query(PlanCatalog).filter(PlanCatalog.code == plan["code"]).first()
            if existing:
                existing.included_users = int(plan["included_users"])
                existing.extra_seat_price = float(plan["extra_seat_price"])
                existing.price = float(plan["price"])
                self.db.add(existing)
                continue
            record = PlanCatalog(
                code=plan["code"],
                name=plan["name"],
                price=float(plan["price"]),
                currency=plan["currency"],
                interval=plan["interval"],
                tier=plan["tier"],
                included_users=int(plan["included_users"]),
                extra_seat_price=float(plan["extra_seat_price"]),
                features=json.dumps(plan["features"]),
                stripe_price_id=plan["stripe_price_id"],
                is_active=True,
            )
            self.db.add(record)
            created.append(record)

        if created:
            self.db.commit()
            for item in created:
                self.db.refresh(item)
        else:
            self.db.commit()

        return self.db.query(PlanCatalog).filter(PlanCatalog.is_active.is_(True)).order_by(PlanCatalog.id).all()

    def list_plans(self) -> List[PlanItem]:
        self.ensure_default_plans()
        items = self.db.query(PlanCatalog).filter(PlanCatalog.is_active.is_(True)).order_by(PlanCatalog.id).all()
        response: List[PlanItem] = []
        for plan in items:
            features = json.loads(plan.features) if plan.features else []
            response.append(
                PlanItem(
                    code=plan.code,
                    name=plan.name,
                    price=float(plan.price),
                    currency=plan.currency,
                    interval=plan.interval,
                    tier=plan.tier,
                    included_users=int(plan.included_users or 1),
                    extra_seat_price=float(plan.extra_seat_price or 0.0),
                    features=features,
                    stripe_price_id=plan.stripe_price_id,
                )
            )
        return response

    def get_plan_by_code(self, plan_code: str) -> PlanCatalog:
        self.ensure_default_plans()
        return self.db.query(PlanCatalog).filter(PlanCatalog.code == plan_code, PlanCatalog.is_active.is_(True)).first()

    def calculate_institution_total(self, plan_code: str, total_users: int) -> float:
        plan = self.get_plan_by_code(plan_code)
        if not plan:
            raise ValueError(f"El plan '{plan_code}' no existe o no está habilitado.")

        included_users = int(getattr(plan, "included_users", 1) or 1)
        extra_seat_price = float(getattr(plan, "extra_seat_price", 0.0) or 0.0)
        extra_users = max(0, int(total_users) - included_users)
        return float(plan.price) + (extra_users * extra_seat_price)

    def add_institution_member(
        self,
        institution_name: str,
        member_name: str,
        member_email: str,
        role: str = "operador",
        total_users: int = 1,
    ):
        role = role.strip().lower()
        if role not in {"operador", "analista", "coordinador"}:
            raise ValueError("El rol debe ser operador, analista o coordinador.")
        existing_member = self.db.query(InstitutionMember).filter(
            InstitutionMember.institution_name == institution_name,
            InstitutionMember.email == member_email,
        ).first()
        if existing_member is not None and getattr(existing_member, "email", None) == member_email:
            raise ValueError("El correo ya pertenece a esta cuenta institucional.")
        plan = self.get_plan_by_code("enterprise")
        if not plan:
            plan = self.get_plan_by_code("pro") or self.get_plan_by_code("free")

        monthly_price = self.calculate_institution_total(plan.code if plan else "enterprise", total_users)

        institution = self.db.query(InstitutionAccount).filter(InstitutionAccount.institution_name == institution_name).first()
        if not institution:
            institution = InstitutionAccount(
                institution_name=institution_name,
                plan_code=plan.code if plan else "enterprise",
                included_users=int(getattr(plan, "included_users", 1) or 1),
                extra_seat_price=float(getattr(plan, "extra_seat_price", 0.0) or 0.0),
                monthly_total=monthly_price,
                is_active=True,
            )
            self.db.add(institution)
            self.db.commit()
            self.db.refresh(institution)
        else:
            institution.plan_code = plan.code if plan else "enterprise"
            institution.included_users = int(getattr(plan, "included_users", 1) or 1)
            institution.extra_seat_price = float(getattr(plan, "extra_seat_price", 0.0) or 0.0)
            institution.monthly_total = monthly_price
            self.db.add(institution)

        member = InstitutionMember(
            institution_name=institution_name,
            member_name=member_name,
            email=member_email,
            role=role,
            is_active=True,
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)

        return {
            "id": member.id,
            "institution_name": institution_name,
            "member_name": member_name,
            "member_email": member_email,
            "role": role,
            "is_active": True,
            "monthly_price": float(monthly_price),
            "created_at": member.created_at.isoformat() if member.created_at else None,
        }

    def create_institution_invite(
        self, institution_name: str, member_name: str, member_email: str, role: str
    ):
        role = role.strip().lower()
        if role not in {"operador", "analista", "coordinador"}:
            raise ValueError("El rol debe ser operador, analista o coordinador.")
        account = self.db.query(InstitutionAccount).filter(
            InstitutionAccount.institution_name == institution_name,
            InstitutionAccount.is_active.is_(True),
        ).first()
        if not account:
            raise ValueError("La cuenta institucional no existe o está desactivada.")
        if self.db.query(Usuario).filter(Usuario.usuario == member_email).first():
            raise ValueError("Ya existe una cuenta con ese correo.")
        pending = self.db.query(InstitutionInvite).filter(
            InstitutionInvite.institution_name == institution_name,
            InstitutionInvite.email == member_email,
            InstitutionInvite.accepted_at.is_(None),
            InstitutionInvite.expires_at > datetime.utcnow(),
        ).first()
        if pending:
            raise ValueError("Ya existe una invitación vigente para ese correo.")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=48)
        invite = InstitutionInvite(
            institution_name=institution_name,
            member_name=member_name,
            email=member_email,
            role=role,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            expires_at=expires_at,
        )
        self.db.add(invite)
        self.db.commit()
        self.db.refresh(invite)
        active_members = self.db.query(InstitutionMember).filter(
            InstitutionMember.institution_name == institution_name,
            InstitutionMember.is_active.is_(True),
        ).count()
        pending_invites = self.db.query(InstitutionInvite).filter(
            InstitutionInvite.institution_name == institution_name,
            InstitutionInvite.accepted_at.is_(None),
            InstitutionInvite.expires_at > datetime.utcnow(),
        ).count()
        pricing = self.get_institution_pricing(institution_name)
        monthly_total = self.calculate_institution_total(
            account.plan_code, max(1, active_members + pending_invites + 1)
        )
        account.monthly_total = monthly_total
        self.db.add(account)
        self.db.commit()
        return {
            "id": invite.id,
            "institution_name": institution_name,
            "member_name": member_name,
            "member_email": member_email,
            "role": role,
            "invitation_url": f"{settings.APP_BASE_URL.rstrip('/')}/?invite={token}",
            "expires_at": expires_at.isoformat(),
            "monthly_price": max(pricing.monthly_total, monthly_total),
        }

    def get_institution_pricing(self, institution_name: str) -> InstitutionPricingResponse:
        institution = self.db.query(InstitutionAccount).filter(InstitutionAccount.institution_name == institution_name).first()
        if not institution:
            plan = self.get_plan_by_code("enterprise") or self.get_plan_by_code("pro")
            included_users = int(getattr(plan, "included_users", 1) or 1)
            extra_seat_price = float(getattr(plan, "extra_seat_price", 0.0) or 0.0)
            count = self.db.query(InstitutionMember).filter(InstitutionMember.institution_name == institution_name).count() if hasattr(self.db, 'query') else 0
            total_users = max(1, count + 1)
            total = self.calculate_institution_total(plan.code if plan else "enterprise", total_users)
            return InstitutionPricingResponse(
                institution_name=institution_name,
                plan_code=plan.code if plan else "enterprise",
                included_users=included_users,
                total_users=total_users,
                extra_users=max(0, total_users - included_users),
                extra_seat_price=extra_seat_price,
                monthly_total=total,
                currency="PEN",
            )

        count = self.db.query(InstitutionMember).filter(InstitutionMember.institution_name == institution_name, InstitutionMember.is_active.is_(True)).count()
        pending_invites = self.db.query(InstitutionInvite).filter(
            InstitutionInvite.institution_name == institution_name,
            InstitutionInvite.accepted_at.is_(None),
            InstitutionInvite.expires_at > datetime.utcnow(),
        ).count()
        total_users = max(1, count + pending_invites + 1)
        total = self.calculate_institution_total(institution.plan_code or "enterprise", total_users)
        return InstitutionPricingResponse(
            institution_name=institution.institution_name,
            plan_code=institution.plan_code,
            included_users=institution.included_users,
            total_users=total_users,
            extra_users=max(0, total_users - institution.included_users),
            extra_seat_price=institution.extra_seat_price,
            monthly_total=total,
            currency="PEN",
        )

    def list_institution_members(self, institution_name: str) -> List[InstitutionMemberResponse]:
        members = self.db.query(InstitutionMember).filter(
            InstitutionMember.institution_name == institution_name,
        ).order_by(InstitutionMember.created_at.desc()).all()
        pricing = self.get_institution_pricing(institution_name)
        response = []
        for member in members:
            response.append(
                InstitutionMemberResponse(
                    id=member.id,
                    institution_name=member.institution_name,
                    member_name=member.member_name,
                    member_email=member.email,
                    role=member.role,
                    is_active=member.is_active,
                    monthly_price=float(pricing.monthly_total),
                    created_at=member.created_at.isoformat() if member.created_at else None,
                )
            )
        return response

    def get_institution_account(self, institution_name: str):
        institution = self.db.query(InstitutionAccount).filter(
            InstitutionAccount.institution_name == institution_name
        ).first()
        if not institution:
            raise ValueError("La cuenta institucional no existe.")
        pricing = self.get_institution_pricing(institution_name)
        active_members = self.db.query(InstitutionMember).filter(
            InstitutionMember.institution_name == institution_name,
            InstitutionMember.is_active.is_(True),
        ).count()
        return {
            **pricing.dict(),
            "is_active": bool(institution.is_active),
            "active_members": active_members,
        }

    def update_institution_plan(self, institution_name: str, plan_code: str):
        institution = self.db.query(InstitutionAccount).filter(
            InstitutionAccount.institution_name == institution_name
        ).first()
        if not institution:
            raise ValueError("La cuenta institucional no existe.")
        plan = self.get_plan_by_code(plan_code)
        if not plan:
            raise ValueError("El plan no existe o no está habilitado.")
        active_members = self.db.query(InstitutionMember).filter(
            InstitutionMember.institution_name == institution_name,
            InstitutionMember.is_active.is_(True),
        ).count()
        pending_invites = self.db.query(InstitutionInvite).filter(
            InstitutionInvite.institution_name == institution_name,
            InstitutionInvite.accepted_at.is_(None),
            InstitutionInvite.expires_at > datetime.utcnow(),
        ).count()
        institution.plan_code = plan.code
        institution.included_users = int(plan.included_users or 1)
        institution.extra_seat_price = float(plan.extra_seat_price or 0.0)
        institution.monthly_total = self.calculate_institution_total(
            plan.code, max(1, active_members + pending_invites + 1)
        )
        self.db.add(institution)
        self.db.commit()
        self.db.refresh(institution)
        return self.get_institution_account(institution_name)

    def update_institution_member(
        self, institution_name: str, member_id: int, role: Optional[str], is_active: Optional[bool]
    ):
        member = self.db.query(InstitutionMember).filter(
            InstitutionMember.id == member_id,
            InstitutionMember.institution_name == institution_name,
        ).first()
        if not member:
            raise ValueError("El miembro no existe en esta cuenta institucional.")
        allowed_roles = {"operador", "analista", "coordinador"}
        if role is not None:
            normalized_role = role.strip().lower()
            if normalized_role not in allowed_roles:
                raise ValueError("El rol debe ser operador, analista o coordinador.")
            member.role = normalized_role
            user_account = self.db.query(Usuario).filter(Usuario.usuario == member.email).first()
            if user_account:
                user_account.rol = normalized_role
                self.db.add(user_account)
        if is_active is not None:
            member.is_active = is_active
            user_account = self.db.query(Usuario).filter(Usuario.usuario == member.email).first()
            if user_account:
                user_account.is_active = int(is_active)
                self.db.add(user_account)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        account = self.db.query(InstitutionAccount).filter(
            InstitutionAccount.institution_name == institution_name
        ).first()
        if account:
            pricing = self.get_institution_pricing(institution_name)
            account.monthly_total = pricing.monthly_total
            self.db.add(account)
            self.db.commit()
        pricing = self.get_institution_pricing(institution_name)
        return InstitutionMemberResponse(
            id=member.id,
            institution_name=member.institution_name,
            member_name=member.member_name,
            member_email=member.email,
            role=member.role,
            is_active=member.is_active,
            monthly_price=pricing.monthly_total,
            created_at=member.created_at.isoformat() if member.created_at else None,
        )

    def create_checkout(self, request: CreateCheckoutRequest) -> CheckoutSessionResponse:
        plan = self.get_plan_by_code(request.plan_code)
        if not plan:
            raise ValueError(f"El plan '{request.plan_code}' no existe o no está habilitado.")

        if settings.STRIPE_SECRET_KEY and stripe is not None:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.create(
                mode="payment" if float(plan.price) > 0 else "subscription",
                line_items=[{"price": plan.stripe_price_id or settings.STRIPE_PRICE_ID_PRO, "quantity": 1}] if plan.price > 0 else [],
                success_url=f"{settings.APP_BASE_URL}/?checkout=success&plan={plan.code}&usuario={request.usuario}",
                cancel_url=f"{settings.APP_BASE_URL}/?checkout=cancel&plan={plan.code}&usuario={request.usuario}",
                customer_email=request.usuario + "@georescue.local",
                metadata={"usuario": request.usuario, "plan_code": plan.code},
            )

            subscription = self.db.query(UserSubscription).filter(
                UserSubscription.usuario == request.usuario,
                UserSubscription.plan_code == plan.code,
                UserSubscription.status == "active",
            ).first()
            if not subscription:
                self.db.add(
                    UserSubscription(
                        usuario=request.usuario,
                        plan_code=plan.code,
                        status="pending",
                        provider="stripe",
                        price=float(plan.price),
                        currency=plan.currency,
                        checkout_session_id=session.id,
                        customer_id=session.customer,
                        started_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=30),
                    )
                )
                self.db.commit()

            return CheckoutSessionResponse(
                status="pending",
                provider="stripe",
                plan_code=plan.code,
                usuario=request.usuario,
                checkout_url=session.url,
                message=f"Checkout creado para el plan {plan.name}.",
                requires_manual_confirmation=False,
            )

        subscription = self.db.query(UserSubscription).filter(
            UserSubscription.usuario == request.usuario,
            UserSubscription.plan_code == plan.code,
        ).order_by(UserSubscription.created_at.desc()).first()

        if not subscription:
            subscription = UserSubscription(
                usuario=request.usuario,
                plan_code=plan.code,
                status="active" if plan.price == 0 else "manual_review",
                provider="manual",
                price=float(plan.price),
                currency=plan.currency,
                started_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)

        return CheckoutSessionResponse(
            status="active" if plan.price == 0 else "manual_review",
            provider="manual",
            plan_code=plan.code,
            usuario=request.usuario,
            checkout_url=None,
            message=(
                "El plan está activado en modo de desarrollo local. "
                "Configura STRIPE_SECRET_KEY para habilitar pagos reales en producción."
                if plan.price > 0 else "Plan gratuito activado."
            ),
            requires_manual_confirmation=plan.price > 0,
        )

    def get_user_subscription(self, usuario: str) -> SubscriptionStatusResponse:
        latest = self.db.query(UserSubscription).filter(UserSubscription.usuario == usuario).order_by(UserSubscription.created_at.desc()).first()
        if not latest:
            free_plan = self.get_plan_by_code("free")
            return SubscriptionStatusResponse(
                usuario=usuario,
                plan_code="free",
                status="active",
                provider="system",
                price=float(free_plan.price) if free_plan else 0.0,
                currency="PEN",
                started_at=datetime.utcnow().isoformat(),
                expires_at=None,
            )

        plan = self.get_plan_by_code(latest.plan_code) or self.db.query(PlanCatalog).filter(PlanCatalog.code == latest.plan_code).first()
        return SubscriptionStatusResponse(
            usuario=latest.usuario,
            plan_code=latest.plan_code,
            status=latest.status,
            provider=latest.provider,
            price=float(latest.price or (plan.price if plan else 0.0)),
            currency=latest.currency or (plan.currency if plan else "PEN"),
            started_at=latest.started_at.isoformat() if latest.started_at else None,
            expires_at=latest.expires_at.isoformat() if latest.expires_at else None,
        )
