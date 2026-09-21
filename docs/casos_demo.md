# Casos de demostración y evaluación futura

Estas preguntas se refieren exclusivamente al corpus ficticio NexoDemo. La columna «Esperado» es una referencia humana para evaluar las futuras respuestas, no resultados ya obtenidos por un LLM. En la etapa 1 solo observamos los fragmentos recuperados.

| Pregunta | Evidencia principal | Esperado en la futura respuesta |
| --- | --- | --- |
| ¿Qué significa el error E202? | `technical/errors.md` · segundo factor caducado | Iniciar una solicitud nueva; nunca compartir códigos. |
| He olvidado mi contraseña, ¿qué hago? | `technical/access.md` · contraseña | Portal de identidad y verificación; soporte si no puede completarse. |
| ¿Cuánto dura el bloqueo tras cinco intentos? | `technical/access.md` · cuenta bloqueada | Quince minutos; contactar con soporte si continúa. |
| ¿Qué información incluyo en un ticket? | `policies/escalation.md` · información necesaria | Error, hora, tipo de equipo y pasos probados; excluir secretos. |
| Mi portátil se ha averiado. ¿Puedo usar la VPN desde mi ordenador personal? | `policies/personal_devices.md` · VPN y escritorio virtual | VPN personal prohibida; alternativa virtual con aprobación previa y condiciones. |
| Me aparece E303. ¿Instalar la VPN otra vez en mi ordenador personal lo arregla? | `technical/errors.md` y `policies/personal_devices.md` | E303 indica equipo no administrado; reinstalar no autoriza el acceso. |
| He perdido el móvil del segundo factor. ¿Puedes restablecerlo? | `technical/access.md` y `policies/escalation.md` | Requiere verificación e intervención humana; el asistente no lo ejecuta. |
| ¿Puedo trabajar desde Japón con la VPN? | `policies/remote_access.md` · extranjero | Falta lista de países; aprobación previa del responsable y seguridad. No inventar permiso. |
| ¿Funciona el escritorio virtual en Ubuntu 24.04? | `policies/personal_devices.md` · datos que faltan | El corpus no especifica compatibilidad; consultar a soporte. |
| ¿Qué dirección IP exacta tiene el servidor VPN? | `technical/vpn.md` · aplicación inaccesible | El corpus no contiene direcciones; no inventar una IP. |

Al comparar TF-IDF y embeddings, comprueba si los primeros resultados contienen la evidencia necesaria. Las consultas que cruzan dominios requieren evidencia de ambos, no solo un fragmento relacionado. Después, con generación y agentes, evaluaremos también corrección, respaldo de cada afirmación, abstención, latencia y consumo de tokens.
