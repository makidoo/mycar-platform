"""
Service de notifications SMS.

En mode MOCK (MOCK_SERVICES=True ou pas de clé API) :
  - Le message est loggé en console et enregistré dans NotificationLog
  - Aucun SMS réel n'est envoyé

En production :
  - Brancher ici l'API Nita Transfer, Amana Transfer ou Airtel
  - Définir dans .env : SMS_PROVIDER, SMS_API_KEY, SMS_SENDER_ID
"""
import logging
import os

logger = logging.getLogger(__name__)

MOCK = os.getenv('MOCK_SERVICES', 'True').lower() in ('true', '1', 'yes')
SMS_PROVIDER  = os.getenv('SMS_PROVIDER', 'mock')
SMS_API_KEY   = os.getenv('SMS_API_KEY', '')
SMS_SENDER_ID = os.getenv('SMS_SENDER_ID', 'DGI-NIGER')


def envoyer_sms(telephone: str, message: str, contexte: str = '') -> dict:
    """
    Point d'entrée unique pour l'envoi SMS.
    Retourne {"ok": True/False, "provider": ..., "mock": True/False}
    """
    if MOCK or not SMS_API_KEY:
        return _envoyer_mock(telephone, message, contexte)

    if SMS_PROVIDER == 'nita':
        return _envoyer_nita(telephone, message)
    if SMS_PROVIDER == 'airtel':
        return _envoyer_airtel(telephone, message)

    # Fallback mock si fournisseur inconnu
    return _envoyer_mock(telephone, message, contexte)


def _envoyer_mock(telephone: str, message: str, contexte: str) -> dict:
    logger.info(
        f"[SMS MOCK] → {telephone} | contexte={contexte} | msg={message[:80]}"
    )
    _sauvegarder_log(telephone, message, contexte, statut='MOCK')
    return {'ok': True, 'provider': 'mock', 'mock': True}


def _envoyer_nita(telephone: str, message: str) -> dict:
    """
    Intégration Nita Transfer (à compléter avec les specs API).
    Exemple :
        import requests
        r = requests.post('https://api.nita.ne/sms/send', json={
            'key': SMS_API_KEY,
            'sender': SMS_SENDER_ID,
            'to': telephone,
            'message': message,
        }, timeout=10)
        return {'ok': r.status_code == 200, 'provider': 'nita', 'mock': False}
    """
    logger.warning("[SMS] Nita Transfer : endpoint non configuré, passage en mock.")
    return _envoyer_mock(telephone, message, 'nita_fallback')


def _envoyer_airtel(telephone: str, message: str) -> dict:
    """Intégration Airtel Money (à compléter avec les specs API)."""
    logger.warning("[SMS] Airtel Money : endpoint non configuré, passage en mock.")
    return _envoyer_mock(telephone, message, 'airtel_fallback')


def _sauvegarder_log(telephone: str, message: str, contexte: str, statut: str):
    """Persiste le log SMS en base de données."""
    try:
        from .models import NotificationLog
        NotificationLog.objects.create(
            canal='SMS',
            destinataire=telephone,
            message=message,
            contexte=contexte,
            statut=statut,
        )
    except Exception as e:
        logger.error(f"[SMS] Impossible de sauvegarder le log : {e}")


# ── Helpers métier ────────────────────────────────────────────

def sms_confirmation_paiement(telephone: str, immat: str, montant: float, reference: str):
    msg = (
        f"DGI Niger - Paiement confirme. "
        f"Vignette {immat} renouvelee pour {montant:,.0f} FCFA. "
        f"Ref: {reference}. Merci."
    )
    return envoyer_sms(telephone, msg, 'confirmation_paiement')


def sms_otp(telephone: str, code: str, immat: str):
    msg = f"DGI Niger - Code de verification pour {immat} : {code}. Valable 10 minutes. Ne partagez pas ce code."
    return envoyer_sms(telephone, msg, 'otp')


def sms_rappel_expiration(telephone: str, immat: str, date_fin: str):
    msg = (
        f"DGI Niger - RAPPEL : La vignette de votre vehicule {immat} "
        f"expire le {date_fin}. Renouvelez via la plateforme MY CAR."
    )
    return envoyer_sms(telephone, msg, 'rappel_expiration')


def sms_transfert_approuve(telephone: str, immat: str):
    msg = f"DGI Niger - Le transfert de propriete du vehicule {immat} a ete approuve. Votre dossier est mis a jour."
    return envoyer_sms(telephone, msg, 'transfert_approuve')


def sms_plainte_recue(telephone: str, reference: str):
    msg = f"DGI Niger - Votre plainte {reference} a ete enregistree. Nous la traiterons dans les meilleurs delais."
    return envoyer_sms(telephone, msg, 'plainte_recue')
