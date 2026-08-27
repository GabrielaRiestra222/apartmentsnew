from decimal import Decimal

from django.core.management.base import BaseCommand

from integrations.models import DynamicPricingRule
from organizations.models import Organization
from properties.models import Property


COMMON_RULES = (
    'No se permite fumar.',
    'No se permiten fiestas.',
    'No se admiten mascotas.',
    'Aparcamiento privado sujeto a peticion y disponibilidad; no se publica precio fijo.',
)

COMMON_EQUIPMENT = {
    'kitchen': ['Placa', 'Horno', 'Microondas', 'Frigorifico', 'Congelador', 'Cafetera', 'Tostadora', 'Vajilla y cuberteria'],
    'bathroom': ['Banera', 'Ducha'],
    'multimedia': ['Television', 'Wi-Fi'],
    'other': ['Lavadora', 'Plancha', 'Tabla de planchar', 'Ropa de cama', 'Toallas', 'Edredones y mantas'],
    'outdoor': ['Ascensor', 'Aparcamiento publico cercano bajo consulta'],
    'services': ['Toallas incluidas', 'Sabanas incluidas', 'Posibilidad de limpieza'],
}

ONE_BEDROOM_PRICING = {
    'price_per_night': '50.00',
    'price_15_days': '700.00',
    'price_1_month': '1200.00',
    'price_2_months': '',
    'price_3_5_months': '1100.00',
    'price_6_months': '1050.00',
    'base_price': Decimal('50.00'),
    'pricing_tiers': [
        {'label': '14 noches', 'amount': '700.00', 'unit': 'estancia'},
        {'label': '1 mes', 'amount': '1200.00', 'unit': 'mes'},
        {'label': '3 a 5 meses', 'amount': '1100.00', 'unit': 'mes'},
        {'label': 'Mas de 6 meses', 'amount': '1050.00', 'unit': 'mes'},
    ],
}

TWO_BEDROOM_PRICING = {
    'price_per_night': '57.50',
    'price_15_days': '805.00',
    'price_1_month': '1380.00',
    'price_2_months': '',
    'price_3_5_months': '1265.00',
    'price_6_months': '1207.50',
    'base_price': Decimal('57.50'),
    'pricing_tiers': [
        {'label': '14 noches', 'amount': '805.00', 'unit': 'estancia'},
        {'label': '1 mes', 'amount': '1380.00', 'unit': 'mes'},
        {'label': '3 a 5 meses', 'amount': '1265.00', 'unit': 'mes'},
        {'label': 'Mas de 6 meses', 'amount': '1207.50', 'unit': 'mes'},
        {'label': 'Mas de 6 meses redondeado recomendado', 'amount': '1210.00', 'unit': 'mes'},
    ],
}


def apartment(
    number,
    commercial_name,
    web_title,
    address,
    owner,
    housing_type,
    size_m2,
    floor,
    max_guests,
    rooms,
    beds,
    bathrooms,
    registration,
    construction_year,
    renovation_year,
    short_description,
    description,
    pricing,
    distribution=None,
    equipment=None,
    warnings=None,
    highlighted=None,
    climate='Aire acondicionado con bomba de calor',
    extra_equipment=None,
    is_active=True,
    is_published=True,
):
    merged_equipment = {key: list(value) for key, value in COMMON_EQUIPMENT.items()}
    if equipment:
        for key, values in equipment.items():
            merged_equipment[key] = values

    merged_equipment.update({
        'apartment_number': [str(number)],
        'commercial_name': [commercial_name],
        'web_title': [web_title],
        'owner_name': [owner],
        'rental_type': ['TEMPORADA'],
        'housing_type': [housing_type],
        'climate': [climate],
        'internet': ['Wi-Fi'],
        'parking_note': ['Aparcamiento publico cercano: Parking Colon-Plaza Mayor y Parking Reyes de Espana. Tarifas a consultar.'],
        'contact_phone': ['670 799 027'],
        'incidents_contact': ['Begona, 628 818 515'],
        'contact_email': ['info@apartments.com'],
        'payment_methods': ['Transferencia', 'Tarjeta', 'Stripe en pruebas'],
        'pricing_model': ['seasonal_stay_tiers'],
        'pricing_tiers': pricing['pricing_tiers'],
        'promotional_discount_percent': ['10'],
        'price_15_days': [pricing['price_15_days']],
        'price_1_month': [pricing['price_1_month']],
        'price_2_months': [pricing['price_2_months']] if pricing['price_2_months'] else [],
        'price_3_5_months': [pricing['price_3_5_months']],
        'price_6_months': [pricing['price_6_months']],
    })

    if highlighted:
        merged_equipment['highlighted_feature'] = [highlighted]
    if extra_equipment:
        merged_equipment.update(extra_equipment)

    return {
        'number': str(number),
        'title': commercial_name,
        'description': description,
        'location': short_description,
        'address': address,
        'city': 'Salamanca',
        'province': 'Salamanca',
        'postal_code': address.split(',')[-1].strip().split(' ')[0] if '370' in address else '',
        'country': 'Espana',
        'price_per_night': pricing['price_per_night'],
        'cleaning_fee': '70.00',
        'max_guests': max_guests,
        'rooms': rooms,
        'bathrooms': bathrooms,
        'min_nights': 14,
        'check_in_time': '13:00',
        'check_out_time': '12:00',
        'rules': '\n'.join(COMMON_RULES),
        'tourist_registration_number': registration,
        'size_m2': size_m2,
        'floor': floor,
        'construction_year': construction_year,
        'renovation_year': renovation_year,
        'distribution': distribution or {'living_room': 1, 'bedrooms': rooms, 'kitchen': 1, 'independent_wc': 1},
        'beds': [{'label': bed} for bed in beds],
        'equipment': merged_equipment,
        'warnings': warnings or [],
        'is_active': is_active,
        'is_published': is_published,
        'pricing_base': pricing['base_price'],
    }


def shared_flat(number, commercial_name, address, size_m2, rooms, max_guests, bathrooms, floor,
                renovation_year, short_description, room_price_note, video_url='', warnings=None,
                beds=None, common_areas=None, room_pricing=None, climate='', bathroom_note='',
                terrace_note='', special_room_note=''):
    flat_identifier = f'Piso {number}'
    room_pricing = room_pricing or ['Habitacion individual pequena: 420 EUR/mes',
                                    'Habitacion doble de uso individual: 450 EUR/mes',
                                    'Habitacion grande o con terraza: 500-520 EUR/mes',
                                    'Suite DIBA con bano y terraza privados: 550 EUR/mes']
    equipment = {
        'apartment_number': [flat_identifier],
        'flat_number': [str(number)],
        'commercial_name': [commercial_name],
        'rental_type': ['PISOS_ALQUILADOS_POR_HABITACIONES'],
        'housing_type': ['PISO_COMPARTIDO'],
        'pricing_model': ['room_monthly'],
        'pricing_unit': ['EUR/habitacion/mes'],
        'room_price_note': [room_price_note],
        'room_pricing': room_pricing,
        'price_1_month': [room_price_note],
        'price_15_days': [],
        'price_2_months': [],
        'price_3_5_months': [],
        'price_6_months': [],
        'shared_flat_booking_model': ['Se reserva una habitacion privada y se comparten zonas comunes.'],
        'shared_flat_price_rule': ['No aplicar tarifas de 14 noches ni precio de apartamento completo.'],
        'utilities_policy': ['Pendiente: incluidos, no incluidos o incluidos hasta un limite mensual.'],
        'deposit_policy': ['Pendiente de definir; recomendacion inicial: una mensualidad.'],
        'kitchen': ['Cocina equipada', 'Microondas', 'Nevera', 'Congelador', 'Cafetera', 'Tostadora', 'Cuberteria'],
        'bathroom': [bathroom_note or f'{bathrooms} banos/aseos con ducha'],
        'multimedia': ['Television', 'Wi-Fi'],
        'other': ['Lavadora', 'Plancha', 'Tabla de planchar', 'Ropa de cama', 'Edredones y mantas'],
        'outdoor': ['Ascensor', *([terrace_note] if terrace_note else [])],
        'common_areas': common_areas or ['Salon-cocina'],
        'services': ['Toallas incluidas', 'Sabanas incluidas', 'Posibilidad de limpieza'],
        'parking_note': ['Aparcamiento bajo peticion y no incluido.'],
        'pets_policy': ['No se admiten mascotas.'],
        'smoking_policy': ['No se permite fumar.'],
    }
    if climate:
        equipment['climate'] = [climate]
    if special_room_note:
        equipment['special_room'] = [special_room_note]
    if video_url:
        equipment['video_url'] = [video_url]

    return {
        'number': flat_identifier,
        'title': commercial_name,
        'description': short_description,
        'location': short_description,
        'address': address,
        'city': 'Salamanca',
        'province': 'Salamanca',
        'postal_code': address.split(',')[-1].strip().split(' ')[0] if '370' in address else '',
        'country': 'Espana',
        'price_per_night': '0.00',
        'cleaning_fee': '0.00',
        'max_guests': max_guests,
        'rooms': rooms,
        'bathrooms': bathrooms,
        'min_nights': 30,
        'check_in_time': '13:00',
        'check_out_time': '12:00',
        'rules': '\n'.join(COMMON_RULES),
        'tourist_registration_number': '',
        'size_m2': size_m2,
        'floor': floor,
        'construction_year': 1975,
        'renovation_year': renovation_year,
        'distribution': {'living_room': 1, 'bedrooms': rooms, 'kitchen': 1, 'independent_wc': bathrooms},
        'beds': [{'label': bed} for bed in (beds or [f'{rooms} camas segun habitaciones'])],
        'equipment': equipment,
        'warnings': warnings or [],
        'is_active': True,
        'is_published': False,
        'pricing_base': Decimal('0.00'),
    }


APARTMENTS = [
    apartment(1, 'Rua Mayor 14 - 3 A', 'Apartamento Rua Mayor, en pleno centro de Salamanca',
              'Calle Rua Mayor, 14, 3 A, 37001 Salamanca', 'Eduardo',
              'Apartamento de una habitacion', None, '3 de 4', 3, 1,
              ['Cama doble pendiente de confirmar', 'Sofa cama o cama supletoria pendiente de confirmar'], 1, '', 1995, None,
              'Apartamento de temporada en Rua Mayor, en pleno centro de Salamanca.',
              'Apartamento de temporada situado en Calle Rua Mayor 14, 3 A, en pleno centro historico de Salamanca. Dispone de un dormitorio, salon con cocina integrada y un bano. La ficha comercial definitiva queda pendiente de completar con metros cuadrados, equipamiento exacto, numero de registro y calendario actualizado.',
              ONE_BEDROOM_PRICING,
              warnings=[
                  'Nombre comercial definitivo pendiente.',
                  'Descripcion corta y completa pendientes de pulir.',
                  'Metros cuadrados pendientes.',
                  'Equipamiento exacto de cocina y bano pendiente.',
                  'Numero de registro pendiente.',
                  'Referencia catastral pendiente para uso interno.',
                  'Calendario actualizado de ocupacion y reservas pendiente.',
                  'Politica de cancelacion pendiente.',
                  'Forma y calendario de cobro para estancias de varios meses pendiente.',
                  'Tarifa para estancias de mas de un mes y menos de tres meses pendiente.',
                  'Confirmar si la limpieza de 70 EUR se anade al precio mostrado o va incluida.',
                  'Comisiones, disputas, devoluciones y fraude de Stripe pendientes de revisar antes de activar cobros reales.',
              ],
              highlighted='Ubicacion en Rua Mayor',
              extra_equipment={
                  'public_title': ['Apartamento Rua Mayor, en pleno centro de Salamanca'],
                  'commercial_name_status': ['Provisional hasta elegir nombre definitivo'],
                  'surface_status': ['Pendiente de incorporar'],
                  'living_room': ['1 con cocina integrada'],
                  'reception': ['Check-in personal coordinado por Begona'],
                  'check_in_window': ['De 13:00 a 18:00/19:00'],
                  'check_out_window': ['Hasta las 12:00'],
                  'deposit_policy': [
                      '14 noches a menos de 1 mes: un tercio del importe de la estancia',
                      '1 a 3 meses: una mensualidad',
                      'Mas de 3 meses: una mensualidad y media',
                  ],
                  'payment_methods': ['Transferencia bancaria', 'Tarjeta mediante Stripe', 'Apple Pay y Google Pay via Stripe', 'Bizum pendiente/manual', 'Efectivo pendiente de decidir', 'Stripe inicialmente en modo de prueba'],
                  'house_rules': [
                      'No esta permitido fumar',
                      'No se admiten mascotas',
                      'No se permiten fiestas ni eventos',
                      'Respetar el descanso de los vecinos',
                      'Evitar ruidos, especialmente durante horario nocturno',
                      'Respetar el maximo de 3 huespedes',
                      'Comunicar cualquier incidencia a Begona',
                      'Cuidar el mobiliario y devolver el apartamento en condiciones adecuadas',
                  ],
                  'faq': [
                      'Como se realiza el check-in? La recepcion es personal. Antes de la llegada, Begona contactara con el huesped para acordar la hora y entregar las llaves.',
                      'Hay aparcamiento? El apartamento no dispone de plaza propia, pero existen varios aparcamientos publicos proximos.',
                      'Se admiten mascotas? No, actualmente no se admiten mascotas.',
                      'Cual es la estancia minima? La estancia minima es de 14 noches.',
                      'Se puede fumar? No esta permitido fumar dentro del apartamento.',
                  ],
                  'pending_fields': [
                      'Nombre comercial definitivo',
                      'Titulo atractivo para el anuncio',
                      'Descripcion corta',
                      'Descripcion completa',
                      'Metros cuadrados',
                      'Equipamiento exacto de cocina y bano',
                      'Numero de registro correspondiente',
                      'Referencia catastral solo para uso interno',
                      'Calendario actualizado de ocupacion y reservas',
                      'Politica de cancelacion',
                      'Forma y calendario de cobro para estancias de varios meses',
                      'Tarifa para estancias de uno a tres meses',
                  ],
              }),
    apartment(2, 'Mirador de la Rua - 2 A', 'Apartamento con terrazas y vistas a la Catedral',
              'Calle Rua Mayor, 14, 2 A, 37001 Salamanca', 'Toti - falta nombre legal completo',
              'Apartamento de una habitacion', 40, '2 de 4', 3, 1,
              ['Cama doble de 135 x 190 cm', 'Sofa cama'], 1, '37/000158', 1995, 2011,
              'Apartamento centrico de 40 m2 con dos terrazas y vistas a la Catedral.',
              'Acogedor apartamento de una habitacion ubicado en la Rua Mayor, entre la Plaza Mayor y las catedrales. Dispone de salon, dormitorio con cama doble, cocina independiente, cuarto de bano y dos terrazas con vistas a la Catedral. Edificio con ascensor, aire acondicionado con bomba de calor y Wi-Fi.',
              ONE_BEDROOM_PRICING, highlighted='Dos terrazas con vistas a la Catedral'),
    apartment(3, 'Rincon de la Rua - 1 A', 'Apartamento centrico con terrazas junto a la Catedral',
              'Calle Rua Mayor, 14, 1 A, 37001 Salamanca', 'Carlos',
              'Apartamento de una habitacion', 40, '1 de 4', 3, 1,
              ['Cama doble de 135 x 190 cm'], 1, '37/000144', 1995, 2011,
              'Apartamento de una habitacion con dos terrazas y vistas a la Catedral.',
              'Apartamento exterior de 40 m2 situado en Rua Mayor, en pleno centro monumental. Cuenta con salon, dormitorio con cama doble, cocina independiente, cuarto de bano y dos terrazas con vistas a la Catedral. Edificio con ascensor y fachada historica original.',
              ONE_BEDROOM_PRICING, warnings=['La web antigua no recoge sofa cama; ocupacion maxima confirmada en 3 personas.'], highlighted='Dos terrazas con vistas a la Catedral'),
    apartment(4, 'Galeria San Esteban - 2 B', 'Apartamento con galeria junto al convento de San Esteban',
              'Calle San Pablo, 50, 2 B, 37008 Salamanca', 'Enrique',
              'Apartamento de una habitacion', 40, '2 planta', 3, 1,
              ['Cama doble de 135 x 190 cm'], 1, '37/000158 pendiente de comprobar', 1998, 2011,
              'Apartamento con galeria acristalada en la historica calle San Pablo.',
              'Apartamento de 40 m2 situado en la calle San Pablo, junto al convento de San Esteban y a pocos minutos de las catedrales y la Plaza Mayor. Dispone de salon, dormitorio con cama doble, cocina independiente, cuarto de bano y galeria acristalada.',
              ONE_BEDROOM_PRICING, warnings=['Registro turistico coincide con apartamento 2; comprobar.'], highlighted='Galeria acristalada'),
    apartment(5, 'Galeria San Pablo - 1 A', 'Apartamento flexible con galeria en el centro historico',
              'Calle San Pablo, 50, 1 A, 37008 Salamanca', 'Enrique',
              'Apartamento de una habitacion', 40, '1 de 3', 3, 1,
              ['Cama de 180 x 190 cm convertible en dos camas de 90 x 190 cm', 'Sofa cama'], 1, '37/000143', 1998, 2011,
              'Apartamento para hasta tres huespedes con dormitorio adaptable y galeria acristalada.',
              'Comodo apartamento de 40 m2 situado en la calle San Pablo. El dormitorio puede prepararse con cama de matrimonio de 180 cm o dos camas individuales de 90 cm. Tambien dispone de sofa cama, salon, cocina independiente, bano y galeria acristalada.',
              ONE_BEDROOM_PRICING, highlighted='Dormitorio adaptable y galeria acristalada'),
    apartment(6, 'Mirador de San Pablo - 3 B', 'Apartamento de dos dormitorios con vistas a la Catedral',
              'Calle San Pablo, 29, 3 B, 37008 Salamanca', 'Enrique',
              'Apartamento de dos habitaciones', 40, '3 de 3', 3, 2,
              ['Cama doble de 135 x 190 cm', 'Dos camas individuales'], 1, '37/000143 pendiente de comprobar', 1992, 2011,
              'Apartamento de dos dormitorios con ventanal orientado hacia la Catedral.',
              'Apartamento de dos dormitorios ubicado en la calle San Pablo, proximo al convento de San Esteban, las catedrales y la Plaza Mayor. Destaca por sus vistas a la Catedral desde el amplio ventanal.',
              TWO_BEDROOM_PRICING, warnings=['Registro turistico coincide con apartamento 5; comprobar.', 'Limpieza de dos dormitorios pendiente de confirmar si debe subir.'], highlighted='Vistas a la Catedral desde el ventanal',
              climate='Aire acondicionado con bomba de calor y calefaccion electrica'),
    apartment(7, 'Patio de San Pablo - 2 Interior', 'Estudio tranquilo junto al convento de San Esteban',
              'Calle San Pablo, 29, 2 interior, 37008 Salamanca', 'Carlos pendiente de confirmar',
              'Estudio', 40, '2 de 3', 2, 1, ['Cama doble de 135 x 190 cm'], 1, '37/000144', 1992, 2016,
              'Estudio tranquilo de 40 m2 orientado a un patio historico.',
              'Estudio en la calle San Pablo, en pleno centro monumental. Su orientacion a patio historico ofrece un ambiente tranquilo. Dispone de salon-dormitorio, cocina, bano completo, Wi-Fi y aire acondicionado con bomba de calor.',
              ONE_BEDROOM_PRICING, warnings=['La ficha menciona reforma 2016 y 2011; confirmar.'], highlighted='Patio historico'),
    apartment(8, 'Balcones de San Pablo - 2 D', 'Apartamento con tres balcones en el centro historico',
              'Calle San Pablo, 29, 2 D, 37008 Salamanca', 'Fernando pendiente de confirmar',
              'Apartamento de una habitacion', 50, '2 de 3', 2, 1, ['Cama doble de 135 x 190 cm'], 1, '37/000158 pendiente de comprobar', 1998, 2016,
              'Apartamento de 50 m2 con tres balcones junto a San Esteban.',
              'Luminoso apartamento de una habitacion en la calle San Pablo. Sus tres balcones aportan luz natural. Cuenta con salon, dormitorio con cama doble, cocina independiente, bano completo, Wi-Fi, aire acondicionado con bomba de calor y ascensor.',
              ONE_BEDROOM_PRICING, warnings=['Construccion y reforma pendientes de confirmar.'], highlighted='Tres balcones'),
    apartment(9, 'Duplex San Esteban - 3 A', 'Duplex de dos dormitorios con gran balcon',
              'Calle San Pablo, 50, 3 A, 37008 Salamanca', 'Pendiente de indicar',
              'Duplex', 70, '3 de 3', 4, 2, ['Cama doble de 135 x 190 cm', 'Cama doble de 135 x 190 cm', 'Sofa cama'], 2, '37/000158 pendiente de comprobar', 1992, 2014,
              'Duplex de 70 m2 con dos dormitorios, dos banos y amplio balcon.',
              'Espacioso duplex en la calle San Pablo, a pocos pasos del convento de San Esteban y las catedrales. Sus 70 m2 se distribuyen en salon, cocina, dos dormitorios, dos banos y amplio balcon.',
              TWO_BEDROOM_PRICING, warnings=['Aunque existe sofa cama, mantener capacidad oficial en 4 personas.', 'Construccion 1992 contradice otras fichas del edificio; comprobar.'], highlighted='Gran balcon'),
    apartment(10, 'Apartamento 10 - pendiente de ficha', 'Apartamento 10 pendiente de completar',
              '', 'Pendiente de indicar',
              'Apartamento pendiente de clasificar', None, '', 1, 1, ['Cama pendiente de confirmar'], 1, '', None, None,
              'Ficha pendiente de completar.',
              'Apartamento reservado dentro de la numeracion comercial 1-15. Pendiente de completar direccion, propietario, metros cuadrados, distribucion, camas, registro, descripcion, fotos, calendario y condiciones especificas.',
              ONE_BEDROOM_PRICING,
              warnings=['Ficha pendiente de completar. No publicar en web hasta validar todos los datos.'],
              extra_equipment={
                  'pending_fields': ['Direccion', 'Propietario', 'Metros cuadrados', 'Distribucion', 'Camas', 'Registro', 'Descripcion', 'Fotos', 'Calendario', 'Condiciones especificas'],
              },
              is_published=False),
    apartment(11, 'Terraza Interior San Pablo - 3 B', 'Apartamento con terraza interior junto a San Esteban',
              'Calle San Pablo, 50, 3 B, 37008 Salamanca', 'Carlos',
              'Apartamento de una habitacion', 40, '3 de 3', 3, 1, ['Cama doble de 135 x 190 cm', 'Sofa cama'], 1, '37/000144', 1998, 2014,
              'Apartamento de una habitacion con terraza interior.',
              'Apartamento situado en la calle San Pablo. Dispone de salon con sofa cama, dormitorio doble, cocina independiente, bano y terraza interior. Incluye Wi-Fi, ascensor, calefaccion electrica, ropa de cama y toallas.',
              ONE_BEDROOM_PRICING, warnings=['El encabezado menciona aire acondicionado Daikin, pero equipamiento recoge calefaccion electrica; confirmar.'], highlighted='Terraza interior',
              climate='Calefaccion electrica con acumuladores'),
    apartment(12, 'Galeria Interior San Pablo - 1 B', 'Apartamento con galeria interior en el casco historico',
              'Calle San Pablo, 50, 1 B, 37008 Salamanca', 'Eduardo',
              'Apartamento de una habitacion', 40, '1 de 3', 3, 1, ['Cama doble de 135 x 190 cm', 'Cama supletoria'], 1, '37/000145', 1998, 2015,
              'Apartamento para tres huespedes con galeria interior.',
              'Apartamento de 40 m2 en la calle San Pablo. Cuenta con salon, dormitorio con cama doble, cama supletoria, cocina independiente, bano y galeria interior. Dispone de Wi-Fi, television, ascensor y calefaccion electrica.',
              ONE_BEDROOM_PRICING, warnings=['Confirmar si dispone de aire acondicionado Daikin.'], highlighted='Galeria interior',
              climate='Calefaccion electrica con acumuladores'),
    apartment(13, 'Apartamento 13 - pendiente de ficha', 'Apartamento 13 pendiente de completar',
              '', 'Pendiente de indicar',
              'Apartamento pendiente de clasificar', None, '', 1, 1, ['Cama pendiente de confirmar'], 1, '', None, None,
              'Ficha pendiente de completar.',
              'Apartamento reservado dentro de la numeracion comercial 1-15. Pendiente de completar direccion, propietario, metros cuadrados, distribucion, camas, registro, descripcion, fotos, calendario y condiciones especificas.',
              ONE_BEDROOM_PRICING,
              warnings=['Ficha pendiente de completar. No publicar en web hasta validar todos los datos.'],
              extra_equipment={
                  'pending_fields': ['Direccion', 'Propietario', 'Metros cuadrados', 'Distribucion', 'Camas', 'Registro', 'Descripcion', 'Fotos', 'Calendario', 'Condiciones especificas'],
              },
              is_published=False),
    apartment(14, 'Atico de la Rua', 'Atico en la Rua Mayor junto a la Plaza Mayor',
              'Calle Rua Mayor, 14, atico/4, 37001 Salamanca', 'Enrique',
              'Atico de una habitacion', 40, '4 de 4', 3, 1, ['Cama doble de 135 x 190 cm', 'Cama supletoria'], 1, '37/000143', 1995, 2015,
              'Atico de una habitacion en la peatonal Rua Mayor.',
              'Acogedor atico situado en Rua Mayor, entre la Plaza Mayor y las catedrales. Dispone de salon, dormitorio con cama doble, cama supletoria, cocina independiente y bano con ducha. Incluye Wi-Fi y aire acondicionado.',
              ONE_BEDROOM_PRICING, highlighted='Atico en Rua Mayor'),
    apartment(15, 'Galeria San Pablo - 2 A', 'Apartamento con galeria acristalada en el centro',
              'Calle San Pablo, 50, 2 A, 37008 Salamanca', 'Eduardo',
              'Apartamento de una habitacion', 40, '2 de 3', 3, 1, ['Cama doble de 135 x 190 cm', 'Sofa cama'], 1, '37/000145 pendiente de comprobar', 1998, 2016,
              'Apartamento para tres huespedes con galeria acristalada.',
              'Apartamento de una habitacion en la calle San Pablo, a pocos pasos de los principales monumentos de Salamanca. Dispone de salon con sofa cama, dormitorio doble, cocina independiente, bano y galeria acristalada.',
              ONE_BEDROOM_PRICING, warnings=['Registro turistico pendiente de comprobar.'], highlighted='Galeria acristalada'),
]

SHARED_FLATS = [
    shared_flat(10, 'Canalejas 19 - Piso compartido', 'Paseo de Canalejas, 19, 4 A, 37001 Salamanca',
                90, 3, 3, 2, '4 de 8', 2019,
                'Piso compartido de tres habitaciones con terraza, a cinco minutos de la Plaza Mayor.',
                '420-450 EUR/mes por habitacion',
                'https://drive.google.com/file/d/1t_jo0_Vgp7MrMEgSsck3c-BOYhIdkQX7/view?usp=drivesdk',
                beds=['Habitacion con cama de matrimonio de 190 cm',
                      'Habitacion con cama de 135 cm',
                      'Habitacion con cama individual de 90 cm'],
                common_areas=['Salon', 'Cocina', 'Terraza de 10 m2'],
                room_pricing=['Precio orientativo pendiente de asignar por habitacion: 420-450 EUR/mes'],
                bathroom_note='Un bano con ducha de hidromasaje y un segundo lavabo con ducha',
                terrace_note='Terraza de 10 m2',
                warnings=['Asignar precio exacto a cada habitacion.']),
    shared_flat(18, 'Canalejas 98 - Coliving Centro', 'Paseo de Canalejas, 98, 5 izquierda, 37001 Salamanca',
                110, 4, 4, 2, '5 de 8', 2017,
                'Piso compartido reformado de 110 m2 con cuatro habitaciones dobles y dos banos.',
                '420-450 EUR/mes por habitacion',
                'https://drive.google.com/file/d/1yBuAZX6u_PneLCOVVN4rTSb9QuL6U-q4/view?usp=drivesdk',
                beds=['Cuatro camas dobles de 135 x 190 cm'],
                common_areas=['Salon-cocina'],
                room_pricing=['Precio orientativo pendiente de asignar por habitacion: 420-450 EUR/mes'],
                climate='Suelo radiante y refrigerante',
                bathroom_note='2 banos con ducha'),
    shared_flat(19, 'Mirador Canalejas 67', 'Paseo de Canalejas, 67, 6 B, 37001 Salamanca',
                130, 4, 4, 2, '6 de 7', 2017,
                'Piso compartido de 130 m2 con cuatro habitaciones dobles y terraza perimetral de 40 m2.',
                '520 EUR/mes por habitacion',
                beds=['Cuatro camas dobles de 135 x 190 cm'],
                common_areas=['Zonas comunes compartidas'],
                room_pricing=['Habitaciones dobles: aproximadamente 520 EUR/mes por habitacion'],
                terrace_note='Terraza perimetral de 40 m2'),
    shared_flat('19-4B', 'DIBA Coliving - Canalejas 19', 'Paseo de Canalejas, 19, 4 B, 37001 Salamanca',
                150, 5, 5, 3, '4 de 8', 2017,
                'Piso compartido de cinco habitaciones, tres banos y suite DIBA con bano y terraza privados.',
                'Habitaciones estandar 420-450 EUR/mes; Suite DIBA 550 EUR/mes',
                beds=['Cinco camas dobles de 135 x 190 cm'],
                common_areas=['Zonas comunes compartidas', 'Terraza exterior', 'Terraza interior'],
                room_pricing=['Habitaciones estandar: 420-450 EUR/mes',
                              'Suite DIBA con bano y terraza privados: aproximadamente 550 EUR/mes',
                              'Habitacion contigua a suite: tarifa superior pendiente si se ofrece union de espacios'],
                terrace_note='Terraza exterior y terraza interior',
                special_room_note='Suite DIBA de 38 m2 con bano privado y terraza',
                warnings=['La ficha antigua indica mascotas permitidas; pendiente de actualizar, criterio recomendado: no admitir mascotas.',
                          'Fumar: conviene prohibirlo.']),
    shared_flat('PORTUGAL-149-3A', 'Portugal 149 - Piso compartido', 'Avenida de Portugal, 149, 3 A, 37006 Salamanca',
                90, 3, 3, 2, '3 de 8', 2018,
                'Piso compartido de tres habitaciones dobles y dos banos, con salon-cocina de 40 m2.',
                '420-450 EUR/mes por habitacion',
                beds=['Tres camas de 135 x 190 cm'],
                common_areas=['Salon-cocina de 40 m2'],
                room_pricing=['Precio orientativo pendiente de asignar por habitacion: 420-450 EUR/mes'],
                climate='Bomba de calor y aire acondicionado inverter',
                bathroom_note='2 banos'),
]


class Command(BaseCommand):
    help = 'Importa o actualiza el catalogo de apartamentos desde las notas comerciales.'

    def handle(self, *args, **options):
        organization = (
            Organization.objects.filter(name__icontains='Riestra').first()
            or Organization.objects.filter(is_active=True).first()
            or Organization.objects.create(name='Riestra Salamanca', contact_email='info@apartments.com')
        )

        imported = []
        for item in [*APARTMENTS, *SHARED_FLATS]:
            prop, created = self.upsert_property(organization, item)
            self.upsert_pricing_rule(prop, item)
            imported.append((prop.id, prop.title, created))

        for prop_id, title, created in imported:
            marker = 'created' if created else 'updated'
            self.stdout.write(f'{marker}: #{prop_id} {title}')

        self.stdout.write(self.style.SUCCESS(f'Imported/updated {len(imported)} properties.'))

    def upsert_property(self, organization, item):
        prop = self.find_existing(item)
        created = False
        if not prop:
            prop = Property(organization=organization)
            created = True

        prop.organization = organization
        prop.title = item['title']
        prop.description = item['description']
        prop.location = item['location']
        prop.address = item['address']
        prop.price_per_night = item['price_per_night']
        prop.cleaning_fee = item['cleaning_fee']
        prop.max_guests = item['max_guests']
        prop.rooms = item['rooms']
        prop.bathrooms = item['bathrooms']
        prop.min_nights = item['min_nights']
        prop.check_in_time = item['check_in_time']
        prop.check_out_time = item['check_out_time']
        prop.rules = item['rules']
        prop.tourist_registration_number = item['tourist_registration_number']
        prop.size_m2 = item['size_m2']
        prop.floor = item['floor']
        prop.construction_year = item['construction_year']
        prop.renovation_year = item['renovation_year']
        prop.distribution = item['distribution']
        prop.beds = item['beds']
        prop.equipment = item['equipment']
        prop.warnings = item['warnings']
        prop.is_active = item['is_active']
        prop.is_published = item['is_published']
        prop.save()
        return prop, created

    def find_existing(self, item):
        number = str(item['number'])
        for prop in Property.objects.all():
            equipment = prop.equipment or {}
            stored_number = equipment.get('apartment_number')
            if isinstance(stored_number, list) and stored_number and str(stored_number[0]) == number:
                return prop
            if str(stored_number) == number:
                return prop

        legacy_title = f'Apartamento nº {number}'
        prop = Property.objects.filter(title=legacy_title).first()
        if prop:
            return prop

        legacy_lower = {
            '4': 'apartamento n4',
            '15': 'apartamento n15',
        }.get(number)
        if legacy_lower:
            prop = Property.objects.filter(title__iexact=legacy_lower).first()
            if prop:
                return prop

        if item['address']:
            return Property.objects.filter(address=item['address']).first()

        return None

    def upsert_pricing_rule(self, prop, item):
        if item['pricing_base'] == Decimal('0.00'):
            return

        DynamicPricingRule.objects.update_or_create(
            property=prop,
            name='Tarifa comercial importada',
            defaults={
                'base_price': item['pricing_base'],
                'weekend_markup_percent': Decimal('0.00'),
                'occupancy_markup_percent': Decimal('0.00'),
                'last_minute_discount_percent': Decimal('10.00'),
                'provider': 'STAY_LENGTH_TIERS',
                'is_active': True,
            },
        )
