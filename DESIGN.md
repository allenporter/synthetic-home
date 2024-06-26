# Synthetic Home

The initial version of synthetic home was used to create devices for experimenting
with LLMs for summaries. The idea was to create a small language that an LLM can
use to create additional variations of homes to use for testing or generating
training data at a large scale that attempt to be somewhat representative of
real world.

There are additional emerging use cases for enabling developers to either manually
test LLM device actions on their own homes or with their own test homes. And
since we ultimately decided on intents as the LLM API in Home Assistant, there
is a desire to reuse the existing tests from [intent test fixtures](https://github.com/home-assistant/intents/blob/main/tests/) where possible.

## Comparison Intent Test Fixtures

The intent test fixtures were designed for testing NLP to intent calls that are
determininstic from the nlp library. There are some differences in design goals:

| Intent Test Fixtures | Synthetic Home (current) |
| ------------ | ------------------------- |
| Entity based. Entities are not created in home assistant and does not include device information.  | Device based. Allows specifying realistic device information that can be useful to ground LLMs such as make, model, etc. |
| Entities are named by hand. Makes it easier to override and reference in the test, though less realistic for how integrations work. | Entities are not specifically named, instead using the entity naming scheme based on devices built into Home Assistant and not in the fixtures. Harder to reference in tests, but more realistic for how integrations work, which helps catch LLM bugs when it gets confused about multiple entities with the same name but in different patforms. |
| Supports a single entity state for all tests, determined offline. The intent library does not look at the current state when suggesting an intent to call, and the intent implementation will handle the details. | Supports variable device states at runtime.  State changes are reflected across all entities associated with the device e.g. the `lock` and the `binary_sensor` for the same device are in sync. This effectively allows supporting events where history is executed at runtime rather than pre-canned. |
| Floors are supported. | Floors are not currently supported. |
| States are expressed as the entity outputs. For example, binary sensors for device classes are expressed with  states such as 'connected, 'normal', 'closed'.  Requires knowing the device class details and getting them correct. | States expressed as entity inputs e.g. 'True', 'False'. This allows home assistant platforms to convert an input such as `is_on` to the device class output to avoid accidental mistakes. |
| Low level. Simple and flexible, and less opinionated, limited on some use cases. | Higher level. More opinionated and less flexible. |

More generally, the intent test fixure is used to exercise intents only but the synthetic
home dataset evals can handle conversation responses or checking other entity states since
the outputs may not be fixed.

## Approach

The lower level description used by the intent test fixtures is close to the lower level
representation used by the synthetic home custom component internally. We will use the higher
level device based description when creating homes but ultimately it will generate the
lower level description that is similar to the intent test fixture description and
used inside the synthetic home component.

If you want to use the the device description, it can generate the lower level entity descriptions.

If you want to use the low level entity descriptions you can use that too, directly.
