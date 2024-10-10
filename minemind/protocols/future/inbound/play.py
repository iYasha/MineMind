from enum import Enum
from typing import Any

from minemind.mc_types import UUID, Array, Boolean, Double, Float, Int, String, VarInt, nbt
from minemind.mc_types.base import MCType, SocketReader


class Component(MCType):

    class Lore(MCType):

        def __init__(self, lines: Array[nbt.String]):
            self.lines = lines

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            lines_count = await VarInt.from_stream(reader)
            return cls(
                lines=await Array.from_stream(reader, lines_count.int, nbt.String, type_params={'has_name': False}),
            )

    class EnchantmentList(MCType):

        class Enchantment(MCType):

            def __init__(self, type_id: VarInt, level: VarInt):
                self.type_id = type_id
                self.level = level

            @classmethod
            async def from_stream(cls, reader: SocketReader, **kwargs):
                return cls(
                    type_id=await VarInt.from_stream(reader),
                    level=await VarInt.from_stream(reader),
                )

        def __init__(self, enchantments: Array['Component.EnchantmentList.Enchantment'], show_in_tooltip: Boolean):
            self.enchantments = enchantments
            self.show_in_tooltip = show_in_tooltip

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            enchantments_count = await VarInt.from_stream(reader)
            return cls(
                enchantments=await Array.from_stream(reader, enchantments_count.int, cls.Enchantment),
                show_in_tooltip=await Boolean.from_stream(reader),
            )

    class BlockSet(MCType):

        def __init__(self, set_type: VarInt, tag_name: String | None = None, block_ids: Array[VarInt] | None = None):
            self.set_type = set_type
            self.tag_name = tag_name
            self.block_ids = block_ids

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            set_type = await VarInt.from_stream(reader)
            if set_type.int == 0:
                return cls(set_type=set_type, tag_name=await String.from_stream(reader))
            return cls(set_type=set_type, block_ids=await Array.from_stream(reader, set_type.int - 1, VarInt))

    class BlockList(MCType):

        class BlockPredicate(MCType):

            class Property(MCType):

                def __init__(
                    self,
                    name: String,
                    is_exact_match: Boolean,
                    exact_value: String | None = None,
                    min_value: String | None = None,
                    max_value: String | None = None,
                ):
                    self.name = name
                    self.is_exact_match = is_exact_match
                    self.exact_value = exact_value
                    self.min_value = min_value
                    self.max_value = max_value

                @classmethod
                async def from_stream(cls, reader: SocketReader, **kwargs):
                    name = await String.from_stream(reader)
                    is_exact_match = await Boolean.from_stream(reader)
                    if is_exact_match:
                        return cls(
                            name=name,
                            is_exact_match=is_exact_match,
                            exact_value=await String.from_stream(reader),
                        )
                    else:
                        return cls(
                            name=name,
                            is_exact_match=is_exact_match,
                            min_value=await String.from_stream(reader),
                            max_value=await String.from_stream(reader),
                        )

            def __init__(
                self,
                has_blocks: Boolean,
                has_properties: Boolean,
                has_nbt: Boolean,
                blocks: 'Component.BlockSet | None' = None,
                properties: Array[Property] | None = None,
                nbt_data: nbt.NBT | None = None,
            ):
                self.has_blocks = has_blocks
                self.has_properties = has_properties
                self.has_nbt = has_nbt
                self.blocks = blocks
                self.properties = properties
                self.nbt_data = nbt_data

            @classmethod
            async def from_stream(cls, reader: SocketReader, **kwargs):
                has_blocks = await Boolean.from_stream(reader)
                blocks = None
                if has_blocks:
                    blocks = await Component.BlockSet.from_stream(reader)

                has_properties = await Boolean.from_stream(reader)
                properties = None
                if has_properties:
                    properties_count = await VarInt.from_stream(reader)
                    properties = await Array.from_stream(reader, properties_count.int, cls.Property)

                has_nbt = await Boolean.from_stream(reader)
                nbt_data = None
                if has_nbt:
                    nbt_data = await nbt.NBT.from_stream(reader, is_anonymous=True)

                return cls(
                    has_blocks=has_blocks,
                    has_properties=has_properties,
                    has_nbt=has_nbt,
                    blocks=blocks,
                    properties=properties,
                    nbt_data=nbt_data,
                )

        def __init__(self, block_predicates: Array['Component.BlockList.BlockPredicate'], show_in_tooltip: Boolean):
            self.block_predicates = block_predicates
            self.show_in_tooltip = show_in_tooltip

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            block_predicates_count = await VarInt.from_stream(reader)
            return cls(
                block_predicates=await Array.from_stream(reader, block_predicates_count.int, cls.BlockPredicate),
                show_in_tooltip=await Boolean.from_stream(reader),
            )

    class Rarity(int, Enum):
        COMMON = 0
        UNCOMMON = 1
        RARE = 2
        EPIC = 3

    class AttributeModifiersList(MCType):

        class Attribute(MCType):

            def __init__(
                self,
                type_id: VarInt,
                unique_id: UUID,
                name: String,
                value: Double,
                operation: VarInt,  # 0 - add, 1 - multiply base, 2 - multiply total
                slot: VarInt,
                # 0 - Any
                # 1 - Main hand
                # 2 - Off hand
                # 3 - Hand
                # 4 - Feet
                # 5 - Legs
                # 6 - Chest
                # 7 - Head
                # 8 - Armor
                # 9 - Body
            ):
                self.type_id = type_id
                self.unique_id = unique_id
                self.name = name
                self.value = value
                self.operation = operation
                self.slot = slot

            @classmethod
            async def from_stream(cls, reader: SocketReader, **kwargs):
                return cls(
                    type_id=await VarInt.from_stream(reader),
                    unique_id=await UUID.from_stream(reader),
                    name=await String.from_stream(reader),
                    value=await Double.from_stream(reader),
                    operation=await VarInt.from_stream(reader),
                    slot=await VarInt.from_stream(reader),
                )

        def __init__(self, attributes: Array[Attribute], show_in_tooltip: Boolean):
            self.attributes = attributes
            self.show_in_tooltip = show_in_tooltip

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            attributes_count = await VarInt.from_stream(reader)
            return cls(
                attributes=await Array.from_stream(reader, attributes_count.int, cls.Attribute),
                show_in_tooltip=await Boolean.from_stream(reader),
            )

    class PotionEffect(MCType):

        class Detail(MCType):
            def __init__(
                self,
                amplifier: VarInt,
                duration: VarInt,
                ambient: Boolean,
                show_particles: Boolean,
                show_icon: Boolean,
                has_hidden_effect: Boolean,
                hidden_effect: 'Detail | None' = None,
            ):
                self.amplifier = amplifier
                self.duration = duration
                self.ambient = ambient
                self.show_particles = show_particles
                self.show_icon = show_icon
                self.has_hidden_effect = has_hidden_effect
                self.hidden_effect = hidden_effect

            @classmethod
            async def from_stream(cls, reader: SocketReader, **kwargs):
                amplifier = await VarInt.from_stream(reader)
                duration = await VarInt.from_stream(reader)
                ambient = await Boolean.from_stream(reader)
                show_particles = await Boolean.from_stream(reader)
                show_icon = await Boolean.from_stream(reader)
                has_hidden_effect = await Boolean.from_stream(reader)
                hidden_effect = None
                if has_hidden_effect:
                    hidden_effect = await cls.from_stream(reader)
                return cls(
                    amplifier=amplifier,
                    duration=duration,
                    ambient=ambient,
                    show_particles=show_particles,
                    show_icon=show_icon,
                    has_hidden_effect=has_hidden_effect,
                    hidden_effect=hidden_effect,
                )

        def __init__(self, type_id: VarInt, detail: Detail):
            self.type_id = type_id
            self.detail = detail

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            return cls(
                type_id=await VarInt.from_stream(reader),
                detail=await cls.Detail.from_stream(reader),
            )

    class Food(MCType):

        class Effect(MCType):

            def __init__(self, type_id: 'Component.PotionEffect', probability: Float):
                self.type_id = type_id
                self.probability = probability

            @classmethod
            async def from_stream(cls, reader: SocketReader, **kwargs):
                return cls(
                    type_id=await Component.PotionEffect.from_stream(reader),
                    probability=await Float.from_stream(reader),
                )

        def __init__(
            self,
            nutrition: VarInt,
            saturation_modifier: Float,
            can_always_eat: Boolean,
            seconds_to_eat: Float,
            using_converts_to: 'Slot',
            effects: Array[Effect],
        ):
            self.nutrition = nutrition
            self.saturation_modifier = saturation_modifier
            self.can_always_eat = can_always_eat
            self.seconds_to_eat = seconds_to_eat
            self.using_converts_to = using_converts_to
            self.effects = effects

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            nutrition = await VarInt.from_stream(reader)
            saturation_modifier = await Float.from_stream(reader)
            can_always_eat = await Boolean.from_stream(reader)
            seconds_to_eat = await Float.from_stream(reader)
            using_converts_to = await Slot.from_stream(reader)
            effects_count = await VarInt.from_stream(reader)
            effects = await Array.from_stream(reader, effects_count.int, cls.Effect)
            return cls(
                nutrition=nutrition,
                saturation_modifier=saturation_modifier,
                can_always_eat=can_always_eat,
                seconds_to_eat=seconds_to_eat,
                using_converts_to=using_converts_to,
                effects=effects,
            )

    class Tool(MCType):

        class Rule(MCType):
            def __init__(
                self,
                blocks: 'Component.BlockSet',
                has_speed: Boolean,
                has_correct_drop_for_blocks: Boolean,
                speed: Float | None = None,
                correct_drop_for_blocks: Boolean | None = None,
            ):
                self.blocks = blocks
                self.has_speed = has_speed
                self.has_correct_drop_for_blocks = has_correct_drop_for_blocks
                self.speed = speed
                self.correct_drop_for_blocks = correct_drop_for_blocks

            @classmethod
            async def from_stream(cls, reader: SocketReader, **kwargs):
                blocks = await Component.BlockSet.from_stream(reader)
                has_speed = await Boolean.from_stream(reader)
                speed = None
                if has_speed:
                    speed = await Float.from_stream(reader)
                has_correct_drop_for_blocks = await Boolean.from_stream(reader)
                correct_drop_for_blocks = None
                if has_correct_drop_for_blocks:
                    correct_drop_for_blocks = await Boolean.from_stream(reader)
                return cls(
                    blocks=blocks,
                    has_speed=has_speed,
                    has_correct_drop_for_blocks=has_correct_drop_for_blocks,
                    speed=speed,
                    correct_drop_for_blocks=correct_drop_for_blocks,
                )

        def __init__(self, rules: Array[Rule], default_mining_speed: Float, damage_per_block: VarInt):
            self.rules = rules
            self.default_mining_speed = default_mining_speed
            self.damage_per_block = damage_per_block

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            rules_count = await VarInt.from_stream(reader)
            rules = await Array.from_stream(reader, rules_count.int, cls.Rule)
            default_mining_speed = await Float.from_stream(reader)
            damage_per_block = await VarInt.from_stream(reader)
            return cls(
                rules=rules,
                default_mining_speed=default_mining_speed,
                damage_per_block=damage_per_block,
            )

    class DyedColor(MCType):
        def __init__(self, color: Int, show_in_tooltip: Boolean):
            self.color = color
            self.show_in_tooltip = show_in_tooltip

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            return cls(
                color=await Int.from_stream(reader),
                show_in_tooltip=await Boolean.from_stream(reader),
            )

    class Projectiles(MCType):
        def __init__(self, projectiles: Array['Slot']):
            self.projectiles = projectiles

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            projectiles_count = await VarInt.from_stream(reader)
            return cls(
                projectiles=await Array.from_stream(reader, projectiles_count.int, Slot),
            )

    class PotionContent(MCType):

        def __init__(
            self,
            has_potion_id: Boolean,
            has_custom_color: Boolean,
            potion_id: VarInt | None = None,
            custom_color: Int | None = None,
            custom_effects: Array['Component.PotionEffect'] | None = None,
        ):
            self.has_potion_id = has_potion_id
            self.has_custom_color = has_custom_color
            self.potion_id = potion_id
            self.custom_color = custom_color
            self.custom_effects = custom_effects

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            has_potion_id = await Boolean.from_stream(reader)
            potion_id = None
            if has_potion_id:
                potion_id = await VarInt.from_stream(reader)
            has_custom_color = await Boolean.from_stream(reader)
            custom_color = None
            if has_custom_color:
                custom_color = await Int.from_stream(reader)

            custom_effects_number = await VarInt.from_stream(reader)
            custom_effects = await Array[Component.PotionEffect].from_stream(
                reader,
                custom_effects_number.int,
                Component.PotionEffect,
            )
            return cls(
                has_potion_id=has_potion_id,
                has_custom_color=has_custom_color,
                potion_id=potion_id,
                custom_color=custom_color,
                custom_effects=custom_effects,
            )

    class Effect(MCType):

        def __init__(self, type_id: VarInt, duration: VarInt):
            self.type_id = type_id
            self.duration = duration

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            return cls(
                type_id=await VarInt.from_stream(reader),
                duration=await VarInt.from_stream(reader),
            )

    class BookPage(MCType):

        def __init__(self, raw_content: String, has_filtered_content: Boolean, filtered_content: String | None = None):
            self.raw_content = raw_content
            self.has_filtered_content = has_filtered_content
            self.filtered_content = filtered_content

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            raw_content = await String.from_stream(reader)
            has_filtered_content = await Boolean.from_stream(reader)
            filtered_content = None
            if has_filtered_content:
                filtered_content = await String.from_stream(reader)
            return cls(
                raw_content=raw_content,
                has_filtered_content=has_filtered_content,
                filtered_content=filtered_content,
            )

    class ArmorTrim(MCType):

        class Override(MCType):

            def __init__(self, armor_material_type: VarInt, overriden_asset_naame: String):
                self.armor_material_type = armor_material_type
                self.overriden_asset_naame = overriden_asset_naame

            @classmethod
            async def from_stream(cls, reader: SocketReader, **kwargs):
                return cls(
                    armor_material_type=await VarInt.from_stream(reader),
                    overriden_asset_naame=await String.from_stream(reader),
                )

        def __init__(
            self,
            trim_material_type: VarInt,
            trim_pattern_type: VarInt,
            show_in_tooltip: Boolean,
            asset_name: String | None = None,  # Only present if Trim Material Type is 0.
            ingredient: VarInt | None = None,  # Only present if Trim Material Type is 0.
            item_model_index: Float | None = None,  # Only present if Trim Material Type is 0.
            overrides: Array[Override] | None = None,  # Only present if Trim Material Type is 0.
            description: nbt.NBT | None = None,  # Only present if Trim Material Type is 0.
            pattern_asset_name: String | None = None,  # Only present if Trim Pattern Type is 0.
            pattern_template_item: VarInt | None = None,  # Only present if Trim Pattern Type is 0.
            pattern_description: nbt.NBT | None = None,  # Only present if Trim Pattern Type is 0.
            pattern_decal: Boolean | None = None,  # Only present if Trim Pattern Type is 0.
        ):
            self.trim_material_type = trim_material_type
            self.trim_pattern_type = trim_pattern_type
            self.show_in_tooltip = show_in_tooltip
            self.asset_name = asset_name
            self.ingredient = ingredient
            self.item_model_index = item_model_index
            self.overrides = overrides
            self.description = description
            self.pattern_asset_name = pattern_asset_name
            self.pattern_template_item = pattern_template_item
            self.pattern_description = pattern_description
            self.pattern_decal = pattern_decal

        @classmethod
        async def from_stream(cls, reader: SocketReader, **kwargs):
            trim_material_type = await VarInt.from_stream(reader)
            asset_name = None
            ingredient = None
            item_model_index = None
            overrides = None
            description = None
            if trim_material_type.int == 0:
                asset_name = await String.from_stream(reader)
                ingredient = await VarInt.from_stream(reader)
                item_model_index = await Float.from_stream(reader)
                overrides_count = await VarInt.from_stream(reader)
                overrides = await Array.from_stream(reader, overrides_count.int, cls.Override)
                description = await nbt.NBT.from_stream(reader, is_anonymous=True)

            trim_pattern_type = await VarInt.from_stream(reader)
            pattern_asset_name = None
            pattern_template_item = None
            pattern_description = None
            pattern_decal = None
            if trim_pattern_type.int == 0:
                pattern_asset_name = await String.from_stream(reader)
                pattern_template_item = await VarInt.from_stream(reader)
                pattern_description = await nbt.NBT.from_stream(reader, is_anonymous=True)
                pattern_decal = await Boolean.from_stream(reader)

            return cls(
                trim_material_type=trim_material_type,
                trim_pattern_type=trim_pattern_type,
                show_in_tooltip=await Boolean.from_stream(reader),
                asset_name=asset_name,
                ingredient=ingredient,
                item_model_index=item_model_index,
                overrides=overrides,
                description=description,
                pattern_asset_name=pattern_asset_name,
                pattern_template_item=pattern_template_item,
                pattern_description=pattern_description,
                pattern_decal=pattern_decal,
            )

    COMPONENT_TYPES = {
        0: {
            'name': 'minecraft:custom_data',
            'from_stream': lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
        1: {
            'name': 'minecraft:max_stack_size',
            'from_stream': lambda reader: VarInt.from_stream(reader),
        },
        2: {
            'name': 'minecraft:max_damage',
            'from_stream': lambda reader: VarInt.from_stream(reader),
        },
        3: {
            'name': 'minecraft:damage',
            'from_stream': lambda reader: VarInt.from_stream(reader),
        },
        4: {
            'name': 'minecraft:unbreakable',
            'from_stream': lambda reader: Boolean.from_stream(reader),
        },
        5: {
            'name': 'minecraft:custom_name',
            'from_stream': lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
        6: {
            'name': 'minecraft:item_name',
            'from_stream': lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
        7: {
            'name': 'minecraft:lore',
            'from_stream': lambda reader: Component.Lore.from_stream(reader),
        },
        8: {
            'name': 'minecraft:rarity',
            'from_stream': lambda reader: VarInt.from_stream(reader),
        },
        9: {
            'name': 'minecraft:enchantments',
            'from_stream': lambda reader: Component.EnchantmentList.from_stream(reader),
        },
        10: {
            'name': 'minecraft:can_place_on',
            'from_stream': lambda reader: Component.BlockList.from_stream(reader),
        },
        11: {
            'name': 'minecraft:can_break',
            'from_stream': lambda reader: Component.BlockList.from_stream(reader),
        },
        12: {
            'name': 'minecraft:attribute_modifiers',
            'from_stream': lambda reader: Component.AttributeModifiersList.from_stream(reader),
        },
        13: {
            'name': 'minecraft:custom_model_data',
            'from_stream': lambda reader: VarInt.from_stream(reader),
        },
        14: {
            'name': 'minecraft:custom_model_data',
        },
        15: {
            'name': 'minecraft:hide_tooltip',
        },
        16: {
            'name': 'minecraft:repair_cost',
            'from_stream': lambda reader: VarInt.from_stream(reader),
        },
        17: {
            'name': 'minecraft:creative_slot_lock',
        },
        18: {
            'name': 'minecraft:enchantment_glint_override',
            'from_stream': lambda reader: VarInt.from_stream(reader),
        },
        19: {
            'name': 'minecraft:intangible_projectile',
        },
        20: {
            'name': 'minecraft:food',
            'from_stream': lambda reader: Component.Food.from_stream(reader),
        },
        21: {
            'name': 'minecraft:fire_resistant',
        },
        22: {
            'name': 'minecraft:tool',
            'from_stream': lambda reader: Component.Tool.from_stream(reader),
        },
        23: {
            'name': 'minecraft:stored_enchantments',
            'from_stream': lambda reader: Component.EnchantmentList.from_stream(reader),
        },
        24: {
            'name': 'minecraft:dyed_color',
            'from_stream': lambda reader: Component.DyedColor.from_stream(reader),
        },
        25: {
            'name': 'minecraft:map_color',
            'from_stream': lambda reader: Int.from_stream(reader),
        },
        26: {
            'name': 'minecraft:map_id',
            'from_stream': lambda reader: VarInt.from_stream(reader),
        },
        27: {
            'name': 'minecraft:map_decorations',
            'from_stream': lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
        28: {
            'name': 'minecraft:map_post_processing',
            'from_stream': lambda reader: VarInt.from_stream(reader),  # 0 - Lock, 1 - Scale
        },
        29: {
            'name': 'minecraft:charged_projectiles',
            'from_stream': lambda reader: Component.Projectiles.from_stream(reader),
        },
        30: {
            'name': 'minecraft:bundle_contents',
            'from_stream': lambda reader: Component.Projectiles.from_stream(reader),
        },
        31: {
            'name': 'minecraft:potion_contents',
            'from_stream': lambda reader: Component.PotionContent.from_stream(reader),
        },
        32: {
            'name': 'minecraft:suspicious_stew_effects',
            'from_stream': lambda reader: Array[Component.Effect].from_stream(
                reader,
                length=None,
                mc_type=Component.Effect,
            ),
        },
        33: {
            'name': 'minecraft:writable_book_content',
            'from_stream': lambda reader: Array[Component.BookPage].from_stream(
                reader,
                length=None,
                mc_type=Component.BookPage,
            ),
        },
        34: {
            'name': 'minecraft:written_book_content',
            'from_stream': lambda reader: Component.component_not_implemented_error('minecraft:written_book_content'),
        },
        35: {
            'name': 'minecraft:trim',
            'from_stream': lambda reader: Component.ArmorTrim.from_stream(reader),
        },
        36: {
            'name': 'minecraft:debug_stick_state',
            'from_stream': lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
        37: {
            'name': 'minecraft:entity_data',
            'from_stream': lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
        38: {
            'name': 'minecraft:bucket_entity_data',
            'from_stream': lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
        39: {
            'name': 'minecraft:block_entity_data',
            'from_stream': lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
        40: {
            'name': 'minecraft:instrument',
            'from_stream': lambda reader: Component.component_not_implemented_error('minecraft:instrument'),
        },
        41: {
            'name': 'minecraft:ominous_bottle_amplifier',
            'from_stream': lambda reader: VarInt.from_stream(reader),
        },
        42: {
            'name': 'minecraft:jukebox_playable',
            'from_stream': lambda reader: Component.component_not_implemented_error('minecraft:jukebox_playable'),
        },
        43: {
            'name': 'minecraft:recipes',
            'from_stream': lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
        44: {
            'name': 'minecraft:lodestone_tracker',
            'from_stream': lambda reader: lambda reader: Component.component_not_implemented_error(
                'minecraft:lodestone_tracker',
            ),
        },
        45: {
            'name': 'minecraft:firework_explosion',
            'from_stream': lambda reader: lambda reader: Component.component_not_implemented_error(
                'minecraft:firework_explosion',
            ),
        },
        46: {
            'name': 'minecraft:fireworks',
            'from_stream': lambda reader: lambda reader: Component.component_not_implemented_error(
                'minecraft:fireworks',
            ),
        },
        47: {
            'name': 'minecraft:profile',
            'from_stream': lambda reader: lambda reader: Component.component_not_implemented_error('minecraft:profile'),
        },
        48: {
            'name': 'minecraft:note_block_sound',
            'from_stream': lambda reader: lambda reader: String.from_stream(reader),
        },
        49: {
            'name': 'minecraft:banner_patterns',
            'from_stream': lambda reader: lambda reader: Component.component_not_implemented_error(
                'minecraft:banner_patterns',
            ),
        },
        50: {
            'name': 'minecraft:base_color',
            'from_stream': lambda reader: lambda reader: VarInt.from_stream(reader),
        },
        51: {
            'name': 'minecraft:pot_decorations',
            'from_stream': lambda reader: lambda reader: Array[VarInt].from_stream(reader, length=None, mc_type=VarInt),
        },
        52: {
            'name': 'minecraft:container',
            'from_stream': lambda reader: lambda reader: Array[Slot].from_stream(reader, length=None, mc_type=Slot),
        },
        53: {
            'name': 'minecraft:block_state',
            'from_stream': lambda reader: lambda reader: Component.component_not_implemented_error(
                'minecraft:block_state',
            ),
        },
        54: {
            'name': 'minecraft:bees',
            'from_stream': lambda reader: lambda reader: Component.component_not_implemented_error('minecraft:bees'),
        },
        55: {
            'name': 'minecraft:lock',
            'from_stream': lambda reader: lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
        56: {
            'name': 'minecraft:container_loot',
            'from_stream': lambda reader: lambda reader: nbt.NBT.from_stream(reader, is_anonymous=True),
        },
    }

    @classmethod
    def component_not_implemented_error(cls, component_name: str):
        # TODO: Implement all https://wiki.vg/Slot_Data#Structured_components
        raise NotImplementedError(f'Component type {component_name} is not implemented')

    def __init__(self, component_type: VarInt, data: Any):
        self.component_type = component_type
        self.data = data

    @classmethod
    async def from_stream(cls, reader: SocketReader, **kwargs):
        component_type = await VarInt.from_stream(reader)
        component_data_type = cls.COMPONENT_TYPES.get(component_type.int)
        if component_data_type is None:
            raise ValueError(f'Unknown component type: {component_type.int}')
        data_from_stream = component_data_type.get('from_stream')
        if data_from_stream is None:
            data = None
        else:
            data = await data_from_stream(reader)
        return cls(component_type=component_type, data=data)


class Slot(MCType):
    """
    New slot data structure https://wiki.vg/Slot_Data#Structured_components
    """

    def __init__(
        self,
        item_count: VarInt,
        item_id: VarInt | None = None,
        components_count_to_add: VarInt | None = None,
        components_count_to_remove: VarInt | None = None,
        components_to_add: Array[Component] | None = None,
        components_to_remove: Array[VarInt] | None = None,
    ):
        self.item_count = item_count
        self.item_id = item_id
        self.components_count_to_add = components_count_to_add
        self.components_count_to_remove = components_count_to_remove
        self.components_to_add = components_to_add
        self.components_to_remove = components_to_remove

    @classmethod
    async def from_stream(cls, reader: SocketReader, **kwargs):
        item_count = await VarInt.from_stream(reader)
        if item_count.int <= 0:
            return cls(item_count=item_count)
        item_id = await VarInt.from_stream(reader)
        components_count_to_add = await VarInt.from_stream(reader)
        components_count_to_remove = await VarInt.from_stream(reader)
        components_to_add = await Array.from_stream(reader, components_count_to_add.int, Component)
        components_to_remove = await Array.from_stream(reader, components_count_to_remove.int, VarInt)
        return cls(
            item_count=item_count,
            item_id=item_id,
            components_count_to_add=components_count_to_add,
            components_count_to_remove=components_count_to_remove,
            components_to_add=components_to_add,
            components_to_remove=components_to_remove,
        )
