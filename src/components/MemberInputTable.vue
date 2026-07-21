<script setup>
const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  lockedLeaderId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

function createEmptyMember() {
  return {
    name: '',
    studentNo: '',
    college: '',
    major: '',
    isLeader: false,
  }
}

function updateMembers(members) {
  emit('update:modelValue', members)
}

function addMember() {
  const member = createEmptyMember()

  if (props.modelValue.length === 0) {
    member.isLeader = true
  }

  updateMembers([...props.modelValue, member])
}

function updateMember(index, field, value) {
  const members = props.modelValue.map((member, memberIndex) =>
    memberIndex === index ? { ...member, [field]: value } : member,
  )
  updateMembers(members)
}

function selectLeader(index) {
  if (props.lockedLeaderId) return
  const members = props.modelValue.map((member, memberIndex) => ({
    ...member,
    isLeader: memberIndex === index,
  }))
  updateMembers(members)
}

function removeMember(index) {
  if (props.modelValue[index]?.id === props.lockedLeaderId) return
  const removedLeader = Boolean(props.modelValue[index]?.isLeader)
  const members = props.modelValue
    .filter((_, memberIndex) => memberIndex !== index)
    .map((member) => ({ ...member }))

  if (members.length === 1) {
    members[0].isLeader = true
  } else if (removedLeader) {
    members.forEach((member) => {
      member.isLeader = false
    })
  }

  updateMembers(members)
}
</script>

<template>
  <section class="member-input-table" aria-labelledby="member-table-title">
    <div class="member-input-table__header">
      <div>
        <h3 id="member-table-title">团队成员</h3>
        <p>请填写成员信息，并指定一名队长。</p>
      </div>
      <button class="add-button" type="button" @click="addMember">添加成员</button>
    </div>

    <div v-if="modelValue.length" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>姓名</th>
            <th>学号</th>
            <th>学院</th>
            <th>专业</th>
            <th>队长</th>
            <th><span class="visually-hidden">操作</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(member, index) in modelValue" :key="index">
            <td>
              <input
                :value="member.name"
                type="text"
                :aria-label="`第 ${index + 1} 名成员姓名`"
                placeholder="请输入姓名"
                @input="updateMember(index, 'name', $event.target.value)"
              />
            </td>
            <td>
              <input
                :value="member.studentNo"
                type="text"
                :aria-label="`第 ${index + 1} 名成员学号`"
                placeholder="请输入学号"
                @input="updateMember(index, 'studentNo', $event.target.value)"
              />
            </td>
            <td>
              <input
                :value="member.college"
                type="text"
                :aria-label="`第 ${index + 1} 名成员学院`"
                placeholder="请输入学院"
                @input="updateMember(index, 'college', $event.target.value)"
              />
            </td>
            <td>
              <input
                :value="member.major"
                type="text"
                :aria-label="`第 ${index + 1} 名成员专业`"
                placeholder="请输入专业"
                @input="updateMember(index, 'major', $event.target.value)"
              />
            </td>
            <td class="leader-cell">
              <input
                :checked="member.isLeader"
                type="radio"
                name="team-leader"
                :disabled="Boolean(lockedLeaderId)"
                :aria-label="`将第 ${index + 1} 名成员设为队长`"
                @change="selectLeader(index)"
              />
            </td>
            <td>
              <button
                class="remove-button"
                type="button"
                :disabled="member.id === lockedLeaderId"
                @click="removeMember(index)"
              >
                {{ member.id === lockedLeaderId ? '队长锁定' : '删除' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="empty-state">暂无成员，请点击“添加成员”开始填写。</div>
  </section>
</template>

<style scoped>
.member-input-table {
  overflow: hidden;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #fff;
}

.member-input-table__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.member-input-table__header h3 { margin: 0 0 5px; font-size: 18px; }
.member-input-table__header p { margin: 0; color: #64748b; font-size: 14px; }
.table-wrapper { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 10px; border-bottom: 1px solid #e2e8f0; text-align: left; }
th { color: #475569; background: #f8fafc; font-size: 13px; white-space: nowrap; }
tbody tr:last-child td { border-bottom: 0; }
input[type='text'] { min-width: 130px; width: 100%; padding: 9px 10px; border: 1px solid #cbd5e1; border-radius: 8px; font: inherit; }
input[type='text']:focus { border-color: #60a5fa; outline: 3px solid rgba(37, 99, 235, 0.12); }
.leader-cell { text-align: center; }
.leader-cell input { width: 18px; height: 18px; accent-color: #2563eb; cursor: pointer; }
.add-button { padding: 9px 15px; border: 1px solid #2563eb; border-radius: 9px; color: #fff; background: #2563eb; font: inherit; font-weight: 700; cursor: pointer; white-space: nowrap; }
.remove-button { padding: 5px 8px; border: 0; color: #dc2626; background: transparent; font: inherit; font-weight: 700; cursor: pointer; }
.remove-button:disabled { color: #94a3b8; cursor: not-allowed; }
.empty-state { padding: 28px 20px; color: #64748b; text-align: center; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }

@media (max-width: 600px) {
  .member-input-table__header { align-items: stretch; flex-direction: column; }
}
</style>
