# Umbrales iniciales de máscaras

Los umbrales deben calibrarse con el conjunto dorado; no son universales.

- IoU >= 0.985: candidato a PASS.
- IoU 0.970–0.985: REVIEW.
- IoU < 0.970: FAIL.
- Cambio de área > 1.5 %: REVIEW.
- Cambio de componentes relevantes: REVIEW o FAIL.
- Desplazamiento normalizado del centro de caja > 0.005: REVIEW.

Nunca permitas que una puntuación alta compense una pata, barra o tornillo perdido.
