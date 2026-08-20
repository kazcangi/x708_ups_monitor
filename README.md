# Dépôt d'addons Home Assistant — Geekworm X708

Ce dépôt contient un addon Home Assistant pour la carte d'extension UPS
**Geekworm X708** :

- **x708_ups_monitor** : surveillance de la batterie (tension, %) et
  arrêt automatique du Raspberry Pi à 15% de charge.

## Ajouter ce dépôt à Home Assistant

1. **Paramètres → Modules complémentaires → Boutique des modules**
2. Menu (⋮) en haut à droite → **Dépôts**
3. Collez l'URL de ce dépôt (une fois publié sur GitHub, par ex.
   `https://github.com/votre-utilisateur/ha-x708-addon`) et validez.
4. L'addon **X708 UPS Monitor** apparaît alors dans la liste, prêt à
   installer.

## Installation locale (sans GitHub)

Si vous ne souhaitez pas publier sur GitHub, copiez simplement le dossier
`x708_ups_monitor` dans `/addons/` sur votre installation Home Assistant
(accessible via l'addon **Samba share** ou **SSH & Terminal**), puis
actualisez la boutique des modules : l'addon apparaîtra dans la section
**Local add-ons**.

Voir `x708_ups_monitor/README.md` pour la documentation complète.
